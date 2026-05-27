import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from database import get_session
import user_service
from services.evaluation import _calculate_dynamic_price, _run_evaluation_background, _run_vcg_evaluation_background
from utils.helpers import send_large_message, _split_message, _parse_evaluation_input
from core.config import *
logger = logging.getLogger(__name__)

async def _do_evaluation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *args,
) -> int:
    """Helper internal: fire background task untuk evaluasi LLM."""
    status_msg = await update.message.reply_text(
        "⏳ Memproses evaluasi AI...\n"
        "📦 Merakit system prompt...",
    )

    tg_id = update.effective_user.id
    lang_code = context.user_data.get("TARGET_LANGUAGE", "ID")
    tier = context.user_data.get("SELECTED_TIER", "BASIC")
    task_type = context.user_data.get("SELECTED_TASK", "PR")
    subtask = context.user_data.get("SELECTED_SUBTASK")
    final_task = subtask or task_type

    # Lempar ke background task (tracked by application to prevent task loss)
    context.application.create_task(
        _run_evaluation_background(
            update, tg_id, lang_code, tier, final_task, status_msg,
            *args,
        )
    )

    context.user_data['in_evaluation'] = False
    return READY


async def collect_user_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    # Cek format One-Shot
    parsed = _parse_evaluation_input(text)
    if parsed:
        return await _do_evaluation(update, context, *parsed)

    # Append ke buffer
    context.user_data['temp_user_ask'] = (
        context.user_data.get('temp_user_ask', "") + "\n" + text
    ).strip()
    return COLLECTING_USER_ASK


async def collect_single_shot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Mengumpulkan teks dari user untuk task single-shot (PSR, Writing QA).
    Setiap pesan di-append ke buffer temp_single_shot.
    Jika parser berhasil deteksi format lengkap, langsung evaluasi.
    Jika tidak, tunggu /next dari user.
    """
    text = update.message.text

    # Append ke buffer
    context.user_data['temp_single_shot'] = (
        context.user_data.get('temp_single_shot', "") + "\n" + text
    ).strip()

    # Coba one-shot parse dulu — jika semua field terpenuhi, langsung evaluasi
    parsed = _parse_evaluation_input(context.user_data['temp_single_shot'])
    if parsed:
        return await _do_evaluation(update, context, *parsed)

    # Belum lengkap, informasikan user
    buf_len = len(context.user_data['temp_single_shot'])
    await update.message.reply_text(
        f"📨 Teks diterima ({buf_len} karakter terakumulasi).\n"
        "Lanjutkan kirim sisa data, atau ketik **/next** jika sudah selesai.",
        parse_mode="Markdown",
    )
    return COLLECTING_SINGLE_SHOT


async def next_process_single_shot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    /next untuk task single-shot: evaluasi dari buffer temp_single_shot.
    """
    buf = context.user_data.get('temp_single_shot', "").strip()
    if not buf:
        await update.message.reply_text(
            "❌ Belum ada data yang diterima. Kirim input Anda terlebih dahulu."
        )
        return COLLECTING_SINGLE_SHOT

    parsed = _parse_evaluation_input(buf)
    if parsed:
        return await _do_evaluation(update, context, *parsed)

    err_msg = "⚠️ **Format tidak dikenali.**"
    if task_type == "TA_PERSONALIZED_SMART_REPLY":
        err_msg += "\n\nPastikan ada label: Conversation:, User Profiles:, Response A1:, Response B1:"
    elif task_type == "TA_WRITING_TOOLS_WRITING_QA":
        err_msg += "\n\nPastikan ada label: Original Text:, User Query:, Response A:"
    elif task_type == "TA_INTELLIGENT_POLLS":
        err_msg += "\n\nPastikan ada label: Conversation:, Response A:, Response B:"
    elif task_type == "TA_WRITING_TOOLS_CONTEXTUAL_SYNONYMS":
        err_msg += "\n\nPastikan ada label: Original text:, Response A1:, Response B1:"

    await update.message.reply_text(
        f"{err_msg}\n\n"
        f"📦 Data terkumpul saat ini: *{len(buf)} karakter*\n"
        "Kirim data tambahan atau perbaiki format, lalu ketik **/next** lagi.",
        parse_mode="Markdown",
    )
    return COLLECTING_SINGLE_SHOT


async def next_to_resp_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    task_code = context.user_data.get('SELECTED_SUBTASK') or context.user_data.get('SELECTED_TASK', '')
    first_input_name = "User Ask / Input Utama"
    
    if "INTELLIGENT_POLLS" in task_code:
        first_input_name = "Conversation"
    elif "PROOFREAD_V2" in task_code or "CYU_WEBSITE" in task_code:
        first_input_name = "Original Input Text"
    elif "CYU_TOPLINE" in task_code or "CYU_ACTION_ITEMS" in task_code:
        first_input_name = "Instruction & Original Input Text"
    elif "TC" in task_code:
        first_input_name = "User"
    elif "AFM" in task_code:
        first_input_name = "User Input"
    elif "CONTEXTUAL_SYNONYMS" in task_code:
        first_input_name = "Original Text"

    if not context.user_data.get('temp_user_ask'):
        await update.message.reply_text(
            f"❌ Anda belum mengirim **{first_input_name}**. Silakan kirim teksnya dulu.",
            parse_mode="Markdown"
        )
        return COLLECTING_USER_ASK

    if task_code == "AFM_SAFETY_EVALUATION_AFM4":
        context.user_data['dynamic_resps'] = []
        context.user_data['current_dynamic_resp'] = ""
        await update.message.reply_text(
            "📥 **Langkah 2**: Kirim **Response A**.\n"
            "Ketik **/next** untuk lanjut ke Response B, C, dst.\n"
            "Jika sudah selesai, ketik **/proceed** untuk memproses evaluasi.",
            parse_mode="Markdown",
        )
        return COLLECTING_DYNAMIC_RESP
        
    elif task_code == "TA_WRITING_TOOLS_CONTEXTUAL_SYNONYMS":
        context.user_data['dynamic_resps'] = []
        context.user_data['current_dynamic_resp'] = ""
        context.user_data['is_response_b'] = False
        await update.message.reply_text(
            "📥 **Langkah 2**: Kirim **Response A1**.\n"
            "Ketik **/next** untuk lanjut ke A2, A3, dst.\n"
            "Jika sudah selesai Response A, ketik **/jump** untuk mulai mengirim Response B1, B2, dst.\n"
            "Jika sudah selesai semua, ketik **/proceed** untuk memproses evaluasi.",
            parse_mode="Markdown",
        )
        return COLLECTING_DYNAMIC_RESP

    await update.message.reply_text(
        "📥 **Langkah 2/4**: Kirim **Response A**.\n"
        "Setelah selesai, ketik **/next**.",
        parse_mode="Markdown",
    )
    return COLLECTING_RESP_A


async def collect_resp_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data['temp_resp_a'] = (
        context.user_data.get('temp_resp_a', "") + "\n" + text
    ).strip()
    return COLLECTING_RESP_A


async def next_to_resp_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data.get('temp_resp_a'):
        await update.message.reply_text(
            "❌ Anda belum mengirim Response A. Silakan kirim teksnya dulu."
        )
        return COLLECTING_RESP_A

    # Deteksi task type dari subtask atau main task
    task_type = context.user_data.get('SELECTED_SUBTASK') or context.user_data.get('SELECTED_TASK', '')
    optional_b_tasks = ["CYU_ACTION_ITEMS", "CYU_TOPLINE_SUMMARIZATION", "CYU_WEBSITE_TOPIC", "AFM", "TA_INTELLIGENT_POLLS", "AFM_SAFETY_EVALUATION_AFM4"]

    if task_type in optional_b_tasks:
        msg = (
            "📥 **Langkah 3/4**: Kirim **Response B** (Opsional).\n"
            "Ketik **/next** untuk lanjut ke Response C, atau ketik **/skip** jika tidak ada Response B (langsung proses)."
        )
    else:
        msg = (
            "📥 **Langkah 3/4**: Kirim **Response B**.\n"
            "Setelah selesai, ketik **/next**."
        )

    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
    )
    return COLLECTING_RESP_B


async def collect_resp_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data['temp_resp_b'] = (
        context.user_data.get('temp_resp_b', "") + "\n" + text
    ).strip()
    return COLLECTING_RESP_B


async def skip_resp_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    task_type = context.user_data.get('SELECTED_SUBTASK') or context.user_data.get('SELECTED_TASK', '')
    optional_b_tasks = ["CYU_ACTION_ITEMS", "CYU_TOPLINE_SUMMARIZATION", "CYU_WEBSITE_TOPIC", "AFM", "TA_INTELLIGENT_POLLS", "AFM_SAFETY_EVALUATION_AFM4"]

    if task_type not in optional_b_tasks:
        await update.message.reply_text(
            "❌ Response B wajib diisi untuk task ini."
        )
        return COLLECTING_RESP_B

    # Jika skip Response B, otomatis skip Response C juga
    return await process_segmented_input(update, context)


async def next_to_resp_c(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    task_type = context.user_data.get('SELECTED_SUBTASK') or context.user_data.get('SELECTED_TASK', '')
    optional_b_tasks = ["CYU_ACTION_ITEMS", "CYU_TOPLINE_SUMMARIZATION", "CYU_WEBSITE_TOPIC", "AFM", "TA_INTELLIGENT_POLLS", "AFM_SAFETY_EVALUATION_AFM4"]

    if not context.user_data.get('temp_resp_b') and task_type not in optional_b_tasks:
        await update.message.reply_text(
            "❌ Anda belum mengirim Response B. Silakan kirim teksnya dulu."
        )
        return COLLECTING_RESP_B

    await update.message.reply_text(
        "📥 **Langkah 4/4**: Kirim **Response C** (Opsional).\n"
        "Ketik **/next** untuk memproses, atau **/skip** jika tidak ada Response C.",
        parse_mode="Markdown",
    )
    return COLLECTING_RESP_C


async def collect_resp_c(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data['temp_resp_c'] = (
        context.user_data.get('temp_resp_c', "") + "\n" + text
    ).strip()
    return COLLECTING_RESP_C


async def collect_dynamic_resp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data['current_dynamic_resp'] = (
        context.user_data.get('current_dynamic_resp', "") + "\n" + text
    ).strip()
    return COLLECTING_DYNAMIC_RESP


async def next_dynamic_resp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current = context.user_data.get('current_dynamic_resp', "").strip()
    if not current:
        idx = len(context.user_data.get('dynamic_resps', []))
        label = chr(65 + idx)
        await update.message.reply_text(
            f"❌ Anda belum mengirim teks. Silakan kirim teksnya dulu."
        )
        return COLLECTING_DYNAMIC_RESP

    # Save current and move to next
    context.user_data['dynamic_resps'].append(current)
    context.user_data['current_dynamic_resp'] = ""
    
    task_code = context.user_data.get('SELECTED_SUBTASK') or context.user_data.get('SELECTED_TASK', '')
    if task_code == "TA_WRITING_TOOLS_CONTEXTUAL_SYNONYMS":
        resps = context.user_data['dynamic_resps']
        if "__JUMP__" in resps:
            jump_idx = resps.index("__JUMP__")
            count = len(resps) - jump_idx - 1
            next_label = f"B{count + 1}"
        else:
            count = len(resps)
            next_label = f"A{count + 1}"
            
        msg = f"📥 **Response {next_label}**.\nKetik **/next** untuk lanjut, atau **/jump** jika beralih ke B, atau **/proceed** jika selesai."
    else:
        next_idx = len(context.user_data['dynamic_resps'])
        next_label = chr(65 + next_idx)
        msg = f"📥 **Response {next_label}**.\nKetik **/next** untuk lanjut, atau **/proceed** untuk memproses evaluasi."
    
    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
    )
    return COLLECTING_DYNAMIC_RESP


async def jump_dynamic_resp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    task_type = context.user_data.get('SELECTED_SUBTASK') or context.user_data.get('SELECTED_TASK', '')
    if task_type != "TA_WRITING_TOOLS_CONTEXTUAL_SYNONYMS":
        await update.message.reply_text("❌ Perintah **/jump** hanya tersedia untuk task Contextual Synonyms.", parse_mode="Markdown")
        return COLLECTING_DYNAMIC_RESP
        
    current = context.user_data.get('current_dynamic_resp', "").strip()
    if current:
        context.user_data['dynamic_resps'].append(current)
        context.user_data['current_dynamic_resp'] = ""
        
    if not context.user_data.get('dynamic_resps'):
        await update.message.reply_text(
            "❌ Anda belum mengirim Response A. Silakan kirim teksnya dulu."
        )
        return COLLECTING_DYNAMIC_RESP
        
    if "__JUMP__" not in context.user_data['dynamic_resps']:
        context.user_data['dynamic_resps'].append("__JUMP__")
    
    context.user_data['is_response_b'] = True
    
    await update.message.reply_text(
        "✅ **Beralih ke Response B.**\n\n"
        "Silakan kirim Response B1.\n"
        "Ketik **/next** untuk lanjut ke B2, B3, dst.\n"
        "Jika sudah selesai semua, ketik **/proceed**.",
        parse_mode="Markdown",
    )
    return COLLECTING_DYNAMIC_RESP


async def process_dynamic_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current = context.user_data.get('current_dynamic_resp', "").strip()
    if current:
        context.user_data['dynamic_resps'].append(current)
        context.user_data['current_dynamic_resp'] = ""

    task_type = context.user_data.get('SELECTED_SUBTASK') or context.user_data.get('SELECTED_TASK', '')
    
    if task_type == "TA_WRITING_TOOLS_CONTEXTUAL_SYNONYMS":
        resps = context.user_data.get('dynamic_resps', [])
        orig = context.user_data.get('temp_user_ask', "")
        
        if "__JUMP__" in resps:
            jump_idx = resps.index("__JUMP__")
            a_responses = resps[:jump_idx]
            b_responses = resps[jump_idx+1:]
        else:
            a_responses = resps
            b_responses = []
            
        if not a_responses:
            await update.message.reply_text("❌ Data belum lengkap. Anda belum mengirim Response A1.")
            return COLLECTING_DYNAMIC_RESP
            
        if not b_responses:
            await update.message.reply_text("❌ Data belum lengkap. Anda belum mengirim Response B1. Gunakan perintah **/jump** untuk beralih ke Response B.", parse_mode="Markdown")
            return COLLECTING_DYNAMIC_RESP
            
        a1 = a_responses[0] if len(a_responses) > 0 else ""
        a2 = a_responses[1] if len(a_responses) > 1 else ""
        a3 = a_responses[2] if len(a_responses) > 2 else ""
        a4 = a_responses[3] if len(a_responses) > 3 else ""
        
        b1 = b_responses[0] if len(b_responses) > 0 else ""
        b2 = b_responses[1] if len(b_responses) > 1 else ""
        b3 = b_responses[2] if len(b_responses) > 2 else ""
        b4 = b_responses[3] if len(b_responses) > 3 else ""
        
        return await _do_evaluation(update, context, orig, a1, a2, a3, a4, b1, b2, b3, b4)
    else:
        args = [context.user_data.get('temp_user_ask', "")] + context.user_data.get('dynamic_resps', [])
        if len(args) < 2:
            await update.message.reply_text("❌ Data belum lengkap. Anda harus mengirim setidaknya satu Response.")
            return COLLECTING_DYNAMIC_RESP
        return await _do_evaluation(update, context, *args)


async def process_segmented_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Final step: jalankan evaluasi dari buffer yang terkumpul."""
    inputs = [
        context.user_data.get('temp_user_ask', ""),
        context.user_data.get('temp_resp_a', ""),
        context.user_data.get('temp_resp_b', ""),
        context.user_data.get('temp_resp_c', ""),
    ]

    return await _do_evaluation(update, context, *inputs)


async def force_done_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler untuk command /done guna memproses evaluasi secara paksa bila data telah di-input semua tanpa /next."""
    text = update.message.text
    
    # Coba parse dari input gabungan di temp_user_ask
    acc_text = context.user_data.get('temp_user_ask', "")
    parsed = _parse_evaluation_input(acc_text)
    if parsed:
        return await _do_evaluation(update, context, *parsed)
    
    # Coba cek apakah step-by-step args sudah lengkap
    u_ask = context.user_data.get('temp_user_ask', "")
    r_a = context.user_data.get('temp_resp_a', "")
    r_b = context.user_data.get('temp_resp_b', "")
    r_c = context.user_data.get('temp_resp_c', "")
    
    if u_ask and r_a and r_b:
        return await _do_evaluation(update, context, u_ask, r_a, r_b, r_c)
    
    await update.message.reply_text(
        "❌ Data belum lengkap atau format gagal dikenali.\n"
        "Pastikan Anda telah mengisi 'Original Input Text' (atau User Ask), 'Response A', dan 'Response B'.",
        parse_mode="Markdown",
    )
    return COLLECTING_USER_ASK



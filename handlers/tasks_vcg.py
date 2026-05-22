import os
import logging
import base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from database import get_session
import user_service
from services.evaluation import _calculate_dynamic_price, _run_evaluation_background, _run_vcg_evaluation_background
from utils.helpers import send_large_message, _split_message
from core.config import (
    COLLECTING_VCG_PROMPT, COLLECTING_VCG_IMAGE_A, COLLECTING_VCG_IMAGE_B,
    COLLECTING_VCG_IMAGE_C, COLLECTING_VCG_IMAGE_D, COLLECTING_VCG_IMAGE_E,
    COLLECTING_VCG_IMAGE_F, READY,
)
logger = logging.getLogger(__name__)

async def collect_vcg_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima User Prompt + Target Style untuk VCG."""
    tg_id = update.effective_user.id
    text = update.message.text or ""
    logger.info(f"[{tg_id}] Collecting VCG prompt: {text[:50]}...")
    
    context.user_data['temp_user_ask'] = (
        context.user_data.get('temp_user_ask', "") + "\n" + text
    ).strip()
    subtask = context.user_data.get('SELECTED_SUBTASK') or context.user_data.get('SELECTED_TASK', '')
    if subtask == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        msg = "✅ Prompt diterima. Ketik **/next** untuk lanjut kirim **Input Image**."
    elif "MULTI_SIDE" in subtask:
        msg = "✅ Prompt diterima. Ketik **/next** untuk lanjut kirim **Input Image**."
    else:
        msg = "✅ Prompt diterima. Ketik **/next** untuk lanjut kirim **Gambar A**."
        
    await update.message.reply_text(msg, parse_mode="Markdown")
    return COLLECTING_VCG_PROMPT


async def vcg_next_to_image_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Transisi: Prompt → Gambar A."""
    tg_id = update.effective_user.id
    logger.info(f"[{tg_id}] vcg_next_to_image_a triggered")
    if not context.user_data.get('temp_user_ask'):
        await update.message.reply_text(
            "❌ Prompt belum dikirim. Kirim **User Prompt** dulu.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_PROMPT

    subtask = context.user_data.get('SELECTED_SUBTASK') or context.user_data.get('SELECTED_TASK', '')
    if subtask == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        msg = "🖼️ **Langkah 2/7** — Kirim **Input Image** (foto/image)."
    elif "MULTI_SIDE" in subtask:
        msg = "🖼️ **Langkah 2/5** — Kirim **Input Image** (foto/image)."
    else:
        msg = "🖼️ **Langkah 2/4** — Kirim **Gambar A** (foto/image)."

    await update.message.reply_text(msg, parse_mode="Markdown")
    return COLLECTING_VCG_IMAGE_A


async def collect_vcg_image_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima Gambar A (photo) untuk VCG."""
    photo = update.message.photo
    if not photo:
        await update.message.reply_text(
            "❌ Harap kirim sebagai **foto/gambar** (bukan file/dokumen).\n"
            "Kirim ulang Gambar A.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_A

    # Ambil resolusi tertinggi
    file_id = photo[-1].file_id
    context.user_data['vcg_image_a'] = file_id

    subtask = context.user_data.get('SELECTED_SUBTASK') or context.user_data.get('SELECTED_TASK', '')
    if subtask == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        msg = "✅ **Input Image** diterima!\nKetik **/next** untuk lanjut kirim **Selection Mask**."
    elif "MULTI_SIDE" in subtask:
        msg = "✅ **Input Image** diterima!\nKetik **/next** untuk lanjut kirim **Response A**."
    else:
        msg = "✅ **Gambar A** diterima!\nKetik **/next** untuk lanjut kirim Gambar B."

    await update.message.reply_text(msg, parse_mode="Markdown")
    return COLLECTING_VCG_IMAGE_A


async def vcg_next_to_image_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Transisi: Gambar A → Gambar B."""
    if not context.user_data.get('vcg_image_a'):
        await update.message.reply_text(
            "❌ Gambar pertama belum dikirim. Kirim gambarnya dulu.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_A

    subtask = context.user_data.get('SELECTED_SUBTASK') or context.user_data.get('SELECTED_TASK', '')
    if subtask == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        msg = "🖼️ **Langkah 3/7** — Kirim **Selection Mask** (foto/image)."
    elif "MULTI_SIDE" in subtask:
        msg = "🖼️ **Langkah 3/5** — Kirim **Response A** (foto/image)."
    else:
        msg = "🖼️ **Langkah 3/4** — Kirim **Gambar B** (foto/image)."

    await update.message.reply_text(msg, parse_mode="Markdown")
    return COLLECTING_VCG_IMAGE_B


async def collect_vcg_image_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima Gambar B (photo) untuk VCG."""
    photo = update.message.photo
    if not photo:
        await update.message.reply_text(
            "❌ Harap kirim sebagai **foto/gambar** (bukan file/dokumen).\n"
            "Kirim ulang Gambar B.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_B

    file_id = photo[-1].file_id
    context.user_data['vcg_image_b'] = file_id

    subtask = context.user_data.get('SELECTED_SUBTASK') or context.user_data.get('SELECTED_TASK', '')
    if subtask == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        msg = "✅ **Selection Mask** diterima!\nKetik **/next** untuk lanjut kirim **Left Image**."
    elif "MULTI_SIDE" in subtask:
        msg = "✅ **Response A** diterima!\nKetik **/next** untuk lanjut kirim **Response B**."
    else:
        msg = "✅ **Gambar B** diterima!\nKetik **/next** untuk lanjut kirim Gambar C."

    await update.message.reply_text(msg, parse_mode="Markdown")
    return COLLECTING_VCG_IMAGE_B


async def vcg_next_to_image_c(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Transisi: Gambar B → Gambar C."""
    if not context.user_data.get('vcg_image_b'):
        await update.message.reply_text(
            "❌ Gambar kedua belum dikirim. Kirim gambarnya dulu.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_B
    subtask = context.user_data.get("SELECTED_SUBTASK", "")
    if subtask == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        msg = "🖼️ **Langkah 4/7** — Kirim **Left Image** (foto/image)."
    elif subtask == "VCG_PROMPT_REWRITE":
        msg = "🖼️ **Langkah 4/5** — Kirim **Gambar C** (foto/image)."
    elif "MULTI_SIDE" in subtask:
        msg = "🖼️ **Langkah 4/5** — Kirim **Response B** (foto/image)."
    else:
        msg = (
            "🖼️ **Langkah 4/4** — Kirim **Gambar C** (opsional).\n"
            "Atau ketik **/skip** untuk langsung memproses dengan 2 gambar."
        )
    
    await update.message.reply_text(msg, parse_mode="Markdown")
    return COLLECTING_VCG_IMAGE_C


async def collect_vcg_image_c(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima Gambar C (opsional) untuk VCG."""
    photo = update.message.photo
    if not photo:
        await update.message.reply_text(
            "❌ Harap kirim sebagai **foto/gambar** (bukan file/dokumen).\n"
            "Kirim ulang Gambar C, atau ketik **/skip**.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_C

    file_id = photo[-1].file_id
    context.user_data['vcg_image_c'] = file_id
    
    subtask = context.user_data.get("SELECTED_SUBTASK", "")
    if subtask == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        await update.message.reply_text(
            "✅ **Left Image** diterima!\n"
            "Ketik **/next** untuk lanjut kirim **Right Image**.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_C
    elif subtask == "VCG_PROMPT_REWRITE":
        await update.message.reply_text(
            "✅ **Gambar C** diterima!\n"
            "Ketik **/next** untuk lanjut kirim Gambar D.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_C
    elif "MULTI_SIDE" in subtask:
        await update.message.reply_text(
            "✅ **Response B** diterima!\n"
            "Ketik **/next** untuk lanjut kirim **Response C** (opsional) atau **/skip**.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_C
    
    await update.message.reply_text(
        "✅ **Gambar C** diterima!\n"
        "Ketik **/next** untuk memulai evaluasi.",
        parse_mode="Markdown",
    )
    return COLLECTING_VCG_IMAGE_C


async def vcg_next_step_after_image_c(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Transisi: Gambar C → Proses (Default) atau Gambar D."""
    subtask = context.user_data.get("SELECTED_SUBTASK", "")
    if subtask == "VCG_PROMPT_REWRITE" or "MULTI_SIDE" in subtask or subtask == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        return await vcg_next_to_image_d(update, context)
    else:
        return await process_vcg_images(update, context)


async def vcg_next_to_image_d(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Transisi: Gambar C → Gambar D (Khusus Prompt Rewrite)."""
    if not context.user_data.get('vcg_image_c'):
        await update.message.reply_text(
            "❌ Gambar ketiga belum dikirim. Kirim gambarnya dulu.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_C

    subtask = context.user_data.get("SELECTED_SUBTASK", "")
    if subtask == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        msg = "🖼️ **Langkah 5/7** — Kirim **Right Image** (foto/image)."
    elif "MULTI_SIDE" in subtask:
        msg = "🖼️ **Langkah 5/5** — Kirim **Response C** (opsional, foto/image).\nAtau ketik **/skip** jika tidak ada."
    else:
        msg = "🖼️ **Langkah 5/5** — Kirim **Gambar D** (foto/image)."

    await update.message.reply_text(msg, parse_mode="Markdown")
    return COLLECTING_VCG_IMAGE_D


async def collect_vcg_image_d(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima Gambar D (photo) khusus VCG_PROMPT_REWRITE."""
    photo = update.message.photo
    if not photo:
        await update.message.reply_text(
            "❌ Harap kirim sebagai **foto/gambar**.\n"
            "Kirim ulang Gambar D.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_D

    file_id = photo[-1].file_id
    context.user_data['vcg_image_d'] = file_id

    subtask = context.user_data.get("SELECTED_SUBTASK", "")
    if subtask == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        msg = "✅ **Right Image** diterima!\nKetik **/next** untuk lanjut kirim **Left Heatmap**."
    elif "MULTI_SIDE" in subtask:
        msg = "✅ **Response C** diterima!\nKetik **/next** untuk memulai evaluasi."
    else:
        msg = "✅ **Gambar D** diterima!\nKetik **/next** untuk memulai evaluasi."

    await update.message.reply_text(msg, parse_mode="Markdown")
    return COLLECTING_VCG_IMAGE_D

async def vcg_next_step_after_image_d(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Transisi: Gambar D → Proses atau Gambar E (VCG_EDIT_MODEL_DIRECT_MANIPULATION)."""
    subtask = context.user_data.get("SELECTED_SUBTASK", "")
    if subtask == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        return await vcg_next_to_image_e(update, context)
    else:
        return await process_vcg_images(update, context)

async def vcg_next_to_image_e(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data.get('vcg_image_d'):
        await update.message.reply_text(
            "❌ Gambar keempat belum dikirim. Kirim gambarnya dulu.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_D
    msg = "🖼️ **Langkah 6/7** — Kirim **Left Heatmap** (foto/image)."
    await update.message.reply_text(msg, parse_mode="Markdown")
    return COLLECTING_VCG_IMAGE_E

async def collect_vcg_image_e(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo = update.message.photo
    if not photo:
        await update.message.reply_text(
            "❌ Harap kirim sebagai **foto/gambar**.\n"
            "Kirim ulang Left Heatmap.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_E

    file_id = photo[-1].file_id
    context.user_data['vcg_image_e'] = file_id
    msg = "✅ **Left Heatmap** diterima!\nKetik **/next** untuk lanjut kirim **Right Heatmap**."
    await update.message.reply_text(msg, parse_mode="Markdown")
    return COLLECTING_VCG_IMAGE_E

async def vcg_next_step_after_image_e(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Transisi: Gambar E → Gambar F (VCG_EDIT_MODEL_DIRECT_MANIPULATION)."""
    subtask = context.user_data.get("SELECTED_SUBTASK", "")
    if subtask == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        return await vcg_next_to_image_f(update, context)
    else:
        return await process_vcg_images(update, context)

async def vcg_next_to_image_f(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data.get('vcg_image_e'):
        await update.message.reply_text(
            "❌ Gambar kelima belum dikirim. Kirim gambarnya dulu.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_E
    msg = "🖼️ **Langkah 7/7** — Kirim **Right Heatmap** (foto/image)."
    await update.message.reply_text(msg, parse_mode="Markdown")
    return COLLECTING_VCG_IMAGE_F

async def collect_vcg_image_f(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo = update.message.photo
    if not photo:
        await update.message.reply_text(
            "❌ Harap kirim sebagai **foto/gambar**.\n"
            "Kirim ulang Right Heatmap.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_F

    file_id = photo[-1].file_id
    context.user_data['vcg_image_f'] = file_id
    msg = "✅ **Right Heatmap** diterima!\nKetik **/next** untuk memulai evaluasi."
    await update.message.reply_text(msg, parse_mode="Markdown")
    return COLLECTING_VCG_IMAGE_F

async def vcg_next_step_after_image_f(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Transisi: Gambar F → Proses."""
    return await process_vcg_images(update, context)


async def process_vcg_images(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Final step VCG: download gambar dari Telegram dan jalankan evaluasi multimodal."""
    file_id_a = context.user_data.get('vcg_image_a')
    file_id_b = context.user_data.get('vcg_image_b')
    file_id_c = context.user_data.get('vcg_image_c')
    file_id_d = context.user_data.get('vcg_image_d')
    file_id_e = context.user_data.get('vcg_image_e')
    file_id_f = context.user_data.get('vcg_image_f')
    user_prompt = context.user_data.get('temp_user_ask', '')

    if not user_prompt:
        await update.message.reply_text(
            "❌ User Prompt belum diisi. Ketik /cancel dan mulai ulang."
        )
        return READY

    subtask = context.user_data.get("SELECTED_SUBTASK", "")
    if subtask == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        if not file_id_a or not file_id_b or not file_id_c or not file_id_d or not file_id_e or not file_id_f:
            await update.message.reply_text("❌ Keenam gambar (Input, Mask, Left, Right, Left Heatmap, Right Heatmap) harus dikirim.")
            return COLLECTING_VCG_IMAGE_F
    elif "MULTI_SIDE" in subtask:
        if not file_id_a or not file_id_b or not file_id_c:
            await update.message.reply_text("❌ Minimal Input Image, Response A, dan Response B harus dikirim.")
            return COLLECTING_VCG_IMAGE_C
    else:
        if not file_id_a or not file_id_b:
            await update.message.reply_text("❌ Minimal Gambar A dan Gambar B harus dikirim.")
            return COLLECTING_VCG_IMAGE_B

    status_msg = await update.message.reply_text(
        "⏳ Memproses evaluasi VCG...\n"
        "📥 Mengunduh gambar dari Telegram..."
    )

    tg_id = update.effective_user.id
    lang_code = context.user_data.get("TARGET_LANGUAGE", "ID")
    tier = context.user_data.get("SELECTED_TIER", "BASIC")
    subtask = context.user_data.get("SELECTED_SUBTASK")
    main_task = context.user_data.get("SELECTED_TASK", "VCG")
    final_task = subtask or main_task

    # Download gambar sebagai bytes
    try:
        bot_instance = context.bot
        images_b64 = {}
        items = [("A", file_id_a), ("B", file_id_b), ("C", file_id_c), ("D", file_id_d), ("E", file_id_e), ("F", file_id_f)]
        for label, fid in items:
            if fid:
                tg_file = await bot_instance.get_file(fid)
                img_bytes = await tg_file.download_as_bytearray()
                images_b64[label] = base64.b64encode(bytes(img_bytes)).decode("utf-8")
    except Exception as e:
        logger.error(f"VCG image download error: {e}")
        await status_msg.edit_text(
            f"❌ Gagal mengunduh gambar: `{e}`\n"
            "Silakan coba lagi."
        )
        context.user_data['in_evaluation'] = False
        return READY

    await status_msg.edit_text(
        "⏳ Memproses evaluasi VCG...\n"
        f"✅ {len(images_b64)} gambar diunduh\n"
        "📦 Merakit system prompt..."
    )

    # CONC-1 FIX: context.application.create_task() agar PTB bisa track dan
    # gracefully shutdown task ini. asyncio.create_task() tidak di-track PTB.
    context.application.create_task(
        _run_vcg_evaluation_background(
            update, tg_id, lang_code, tier, final_task, status_msg,
            user_prompt, images_b64,
        )
    )
    context.user_data['in_evaluation'] = False
    return READY



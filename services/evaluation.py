import random
import re
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from core.config import TIER_MODELS, READY, TIER_DISPLAY_LABELS
from database import get_session
import user_service
from prompt_assembler import assemble_evaluator_prompt
from kie_api import call_ai_engine
from utils.helpers import send_large_message

logger = logging.getLogger(__name__)

def _calculate_dynamic_price(tier: str, content_len: int = 2000) -> int:
    """
    Menghitung harga dinamis (randomize) berdasarkan tier dan estimasi panjang input.
    Digunakan oleh SEMUA task: PR, TC, CYU, maupun VCG (image-based).
    """
    if tier in ["PREMIUM", "PRO"]:
        if content_len < 1000:
            return random.randint(200, 220)
        elif content_len <= 4000:
            return random.randint(220, 240)
        else:
            return random.randint(240, 250)
    else:  # BASIC
        if content_len < 1000:
            return random.randint(80, 90)
        elif content_len <= 4000:
            return random.randint(90, 105)
        else:
            return random.randint(105, 120)

def _extract_database_content(text: str) -> str:
    """
    Ekstrak konten di antara tag <database> dan </database>.
    Mendukung tag case-insensitive dan multi-line.
    """
    pattern = r"<(?:database|result)>(.*?)</(?:database|result)>"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text  # Fallback: Simpan semua jika tag tidak ditemukan

def _format_user_input(
    task_type: str,
    *args
) -> str:
    """Format user input menjadi payload yang rapi untuk dikirim ke LLM."""
    if len(args) == 6:
        # PSR vs Writing QA (keduanya punya 6 args)
        if task_type == "TA_PERSONALIZED_SMART_REPLY":
            conv, prof, a1, a2, b1, b2 = args
            return (
                f"1. CONVERSATION:\n{conv}\n\n"
                f"2. USER PROFILES:\n{prof}\n\n"
                f"3. RESPONSE A1:\n{a1 or 'N/A'}\n\n"
                f"4. RESPONSE A2:\n{a2 or 'N/A'}\n\n"
                f"5. RESPONSE B1:\n{b1 or 'N/A'}\n\n"
                f"6. RESPONSE B2:\n{b2 or 'N/A'}"
            )
        else:
            # Writing QA (Original, Selected, Query, Resp A, B, C)
            orig, sel, query, ra, rb, rc = args
            return (
                f"1. ORIGINAL TEXT:\n{orig}\n\n"
                f"2. SELECTED TEXT:\n{sel or 'N/A'}\n\n"
                f"3. USER QUERY:\n{query}\n\n"
                f"4. RESPONSE A:\n{ra or 'N/A'}\n\n"
                f"5. RESPONSE B:\n{rb or 'N/A'}\n\n"
                f"6. RESPONSE C:\n{rc or 'N/A'}"
            )

    # Default logic (4 args: user_ask, resp_a, resp_b, resp_c)
    user_ask, resp_a, resp_b, resp_c = args[:4]

    # ── KHUSUS: CYU_ACTION_ITEMS ─────────────────────────────────────────
    # Prompt mengharapkan label: INSTRUCTION & ORIGINAL INPUT TEXT, RESPONSE A/B/C (opsional)
    # Jangan tampilkan RESPONSE B kosong — LLM akan menolak menganalisis jika ada label kosong.
    if task_type == "CYU_ACTION_ITEMS":
        payload = f"INSTRUCTION & ORIGINAL INPUT TEXT:\n{user_ask}\n\nRESPONSE A:\n{resp_a}"
        if resp_b:
            payload += f"\n\nRESPONSE B:\n{resp_b}"
        else:
            payload += "\n\n[Hanya 1 response yang dievaluasi — lewati Pairwise Comparison]"
        if resp_c:
            payload += f"\n\nRESPONSE C:\n{resp_c}"
        return payload

    # ── KHUSUS: CYU_TOPLINE_SUMMARIZATION ────────────────────────────────
    if task_type == "CYU_TOPLINE_SUMMARIZATION":
        payload = f"INSTRUCTION & ORIGINAL INPUT TEXT:\n{user_ask}\n\nRESPONSE A:\n{resp_a}"
        if resp_b:
            payload += f"\n\nRESPONSE B:\n{resp_b}"
        else:
            payload += "\n\n[Hanya 1 response yang dievaluasi — lewati Pairwise Comparison]"
        if resp_c:
            payload += f"\n\nRESPONSE C:\n{resp_c}"
        return payload

    # ── DEFAULT: PR, TC, AFM, CYU website, dan lainnya ───────────────────
    # Berlaku juga untuk AFM (user_ask=User Input, resp_a=Response)
    payload = f"USER ASK:\n{user_ask}\n\nRESPONSE A:\n{resp_a}"
    if resp_b:
        payload += f"\n\nRESPONSE B:\n{resp_b}"
    else:
        payload += "\n\n[Response B tidak disertakan — hanya 1 response yang dievaluasi, lewati Pairwise Comparison]"
    if resp_c:
        payload += f"\n\nRESPONSE C:\n{resp_c}"

    return payload


async def _run_evaluation_background(
    update: Update,
    tg_id: int,
    lang_code: str,
    tier: str,
    task_type: str,
    status_msg,
    *args,
):
    """Fungsi asinkron di belakang layar: prompt assembly → API call → deduct on success."""
    model = TIER_MODELS.get(tier, "gemini-3.1-pro")

    # Hitung harga dinamis berdasarkan panjang total konten
    content_len = sum(len(str(a)) for a in args if a)
    price = _calculate_dynamic_price(tier, content_len)

    # 0. Balance pre-check (double-check)
    async with get_session() as session:
        has_balance = await user_service.check_balance(session, tg_id, price)
    if not has_balance:
        await status_msg.edit_text(
            f"❌ Saldo tidak mencukupi ({price:,} Poin).\n"
            "Hubungi Admin untuk top-up."
        )
        return

    # 1. Rakit evaluator prompt (dengan Critical Thinking persona)
    # Gunakan task_type yang sudah dipass (bisa subtask atau main task)
    final_task_code = task_type

    try:
        evaluator_prompt = assemble_evaluator_prompt(lang_code, final_task_code)
    except FileNotFoundError as e:
        await status_msg.edit_text(f"❌ Error: {e}")
        return

    await status_msg.edit_text(
        "⏳ Memproses evaluasi AI...\n"
        f"✅ Evaluator prompt dirakit ({len(evaluator_prompt)} karakter)\n"
        f"🚀 Memproses dengan AI..."
    )

    # 2. Susun user input payload
    user_input_payload = _format_user_input(task_type, *args)

    # 3. Panggil API LLM — Refund Logic: TIDAK potong saldo jika gagal
    try:
        llm_response = await call_ai_engine(
            evaluator_prompt, user_input_payload, model_override=model
        )
    except Exception as e:
        logger.error(f"API call error: {e}")
        await status_msg.edit_text(
            "❌ **Sistem sibuk, saldo tidak dipotong.**\n"
            "Silakan coba lagi nanti.\n\n"
            f"Detail: `{type(e).__name__}: {e}`"
        )
        return

    # Cek apakah response menunjukkan error (❌) atau peringatan sistem (⚠️)
    if llm_response.startswith(("❌", "⚠️")):
        await status_msg.edit_text(
            "❌ **Sistem sibuk, saldo tidak dipotong.**\n"
            "Silakan coba lagi nanti.\n\n"
            f"{llm_response}"
        )
        return

    await status_msg.edit_text("✅ Respons diterima! Memotong saldo...")

    # 4. SUKSES: Baru potong saldo & Simpan History
    eval_id = 0
    try:
        async with get_session() as session:
            remaining = await user_service.deduct_balance(
                session, tg_id, price, task_type, model
            )
            # ── TASK 1: Simpan History (Hanya bagian <database>) ────────────────
            db_content = _extract_database_content(llm_response)
            eval_record = await user_service.add_evaluation(
                session, tg_id, task_type, user_input_payload, db_content
            )
            if eval_record:
                eval_id = eval_record.id
    except ValueError as e:
        await status_msg.edit_text(f"❌ Gagal potong saldo: {e}")
        return
    except Exception as e:
        logger.error(f"Deduction/History error: {e}")
        await status_msg.edit_text(
            "⚠️ Respons berhasil diterima tapi gagal memproses data saldo/history.\n"
            "Hubungi Admin."
        )
        remaining = 0

    # 5. Kirim hasil akhir ke user
    await status_msg.delete()
    
    disclaimer_html = (
        "⚠️ <b>PENGINGAT</b>: <i>Tugas AI hanya membantu. Harap telaah kembali hasil evaluasi ini "
        "dengan cermat (Critical Thinking required).</i>\n"
        "──────────────────\n"
    )
    
    tier_label = TIER_DISPLAY_LABELS.get(tier, tier)
    footer_html = (
        f"──────────────────\n"
        f"✅ <b>Evaluasi Selesai!</b>\n"
        f"🤖 AI Tier: <b>{tier_label}</b>\n"
        f"💰 Biaya: <b>{price} Poin</b>\n"
        f"💳 Sisa Saldo: <b>{remaining:,} Poin</b>\n"
        f"──────────────────\n"
        f"💡 Ketik <b>/mulai</b> untuk lanjut, atau <b>/cancel</b> untuk ganti task/proyek.\n"
    )
    
    # Tombol Feedback
    reply_markup = None
    if eval_id:
        kb = [[
            InlineKeyboardButton("👍 Akurat", callback_data=f"feed_pos_{eval_id}"),
            InlineKeyboardButton("👎 Kurang", callback_data=f"feed_neg_{eval_id}"),
        ]]
        reply_markup = InlineKeyboardMarkup(kb)

    await send_large_message(
        update, 
        llm_response, 
        disclaimer=disclaimer_html, 
        footer=footer_html, 
        reply_markup=reply_markup
    )

    # ── TASK 4: Low Balance Notification ──────────────────────────
    if remaining < 100:
        await update.message.reply_text(
            f"⚠️ **Sisa saldo Anda hampir habis ({remaining:,} Poin).**\n"
            "Harap hubungi Admin untuk top-up pengerjaan selanjutnya.",
            parse_mode="Markdown"
        )

    return READY
from kie_api import call_ai_engine_multimodal

async def _run_vcg_evaluation_background(
    update: Update,
    tg_id: int,
    lang_code: str,
    tier: str,
    task_type: str,
    status_msg,
    user_prompt: str,
    images_b64: dict,
):
    """Background task: evaluasi VCG multimodal."""
    model = TIER_MODELS.get(tier, "gemini-3.1-pro")
    # VCG: estimasi content_len dari panjang prompt (gambar tidak punya karakter)
    # Gunakan minimum 2000 agar masuk range Medium → harga wajar
    content_len = max(len(user_prompt), 2000)
    price = _calculate_dynamic_price(tier, content_len)

    # Balance pre-check
    async with get_session() as session:
        has_balance = await user_service.check_balance(session, tg_id, price)
    if not has_balance:
        await status_msg.edit_text(
            f"❌ Saldo tidak mencukupi ({price:,} Poin).\nHubungi Admin untuk top-up."
        )
        return

    # Rakit evaluator prompt
    try:
        evaluator_prompt = assemble_evaluator_prompt(lang_code, task_type)
    except FileNotFoundError as e:
        await status_msg.edit_text(f"❌ Error: {e}")
        return

    # Susun user input payload
    if task_type == "VCG_PROMPT_REWRITE":
        instruction_ref = "VCG Prompt Rewrite Variety Review"
    elif "MULTI_SIDE" in task_type:
        instruction_ref = "VCG ADM Multi Side"
    else:
        instruction_ref = "VCG Base Creation & Edit Model"

    if "MULTI_SIDE" in task_type:
        new_images_b64 = {}
        if "A" in images_b64: new_images_b64["Input Image"] = images_b64["A"]
        if "B" in images_b64: new_images_b64["A"] = images_b64["B"]
        if "C" in images_b64: new_images_b64["B"] = images_b64["C"]
        if "D" in images_b64: new_images_b64["C"] = images_b64["D"]
        images_b64 = new_images_b64

        img_count = len(images_b64)

        labels = []
        if "Input Image" in images_b64: labels.append("Input Image")
        if "A" in images_b64: labels.append("Response A")
        if "B" in images_b64: labels.append("Response B")
        if "C" in images_b64: labels.append("Response C")
        img_labels_str = ", ".join(labels)
        
        user_input_text = (
            f"USER PROMPT & TARGET STYLE: {user_prompt}\n\n"
            f"GAMBAR YANG DIEVALUASI: {img_labels_str} ({img_count} gambar)\n\n"
            f"Lakukan evaluasi lengkap sesuai guideline {instruction_ref}."
        )
    else:
        img_count = len(images_b64)
        img_labels = ", ".join(f"Gambar {k}" for k in images_b64.keys())
        user_input_text = (
            f"USER PROMPT: {user_prompt}\n\n"
            f"GAMBAR YANG DIEVALUASI: {img_labels} ({img_count} gambar)\n\n"
            f"Lakukan evaluasi lengkap sesuai guideline {instruction_ref}."
        )

    logger.info(f"[{tg_id}] VCG Evaluation keys sent: {list(images_b64.keys())} - Count: {img_count}")

    await status_msg.edit_text(
        "⏳ Memproses evaluasi VCG...\n"
        f"✅ Evaluator prompt dirakit ({len(evaluator_prompt):,} karakter)\n"
        f"🖼️ Mengirim {img_count} gambar ke AI..."
    )

    # Panggil API multimodal
    try:
        llm_response = await call_ai_engine_multimodal(
            system_prompt=evaluator_prompt,
            user_text=user_input_text,
            images_b64=images_b64,
            model_override=model,
        )
    except Exception as e:
        logger.error(f"VCG API error: {e}")
        await status_msg.edit_text(
            "❌ **Sistem sibuk, saldo tidak dipotong.**\n"
            f"Detail: `{type(e).__name__}: {e}`"
        )
        return

    if llm_response.startswith(("❌", "⚠️")):
        await status_msg.edit_text(
            f"❌ **Sistem error, saldo tidak dipotong.**\n{llm_response}"
        )
        return

    await status_msg.edit_text("✅ Respons VCG diterima! Memotong saldo...")

    # Potong saldo & Simpan History
    eval_id = 0
    try:
        async with get_session() as session:
            remaining = await user_service.deduct_balance(
                session, tg_id, price, task_type, model
            )
            # ── TASK 1: Simpan History (Hanya bagian <database>) ────────────────
            db_content = _extract_database_content(llm_response)
            eval_record = await user_service.add_evaluation(
                session, tg_id, task_type, user_input_text, db_content
            )
            if eval_record:
                eval_id = eval_record.id
    except Exception as e:
        logger.error(f"Deduction/History error: {e}")
        remaining = 0

    await status_msg.delete()

    disclaimer_html = (
        "⚠️ <b>PENGINGAT</b>: <i>Tugas AI hanya membantu. Harap telaah kembali hasil evaluasi ini "
        "dengan cermat (Critical Thinking required).</i>\n"
        "──────────────────\n"
    )
    tier_label = TIER_DISPLAY_LABELS.get(tier, tier)
    footer_html = (
        f"──────────────────\n"
        f"✅ <b>Evaluasi VCG Selesai!</b>\n"
        f"🤖 AI Tier: <b>{tier_label}</b>\n"
        f"💰 Biaya: <b>{price} Poin</b>\n"
        f"💳 Sisa Saldo: <b>{remaining:,} Poin</b>\n"
        f"──────────────────\n"
        f"💡 Ketik <b>/mulai</b> untuk lanjut, atau <b>/cancel</b> untuk ganti task."
    )

    # Tombol Feedback
    reply_markup = None
    if eval_id:
        kb = [[
            InlineKeyboardButton("👍 Akurat", callback_data=f"feed_pos_{eval_id}"),
            InlineKeyboardButton("👎 Kurang", callback_data=f"feed_neg_{eval_id}"),
        ]]
        reply_markup = InlineKeyboardMarkup(kb)

    await send_large_message(
        update, 
        llm_response, 
        disclaimer=disclaimer_html, 
        footer=footer_html, 
        reply_markup=reply_markup
    )

    # ── TASK 4: Low Balance Notification ──────────────────────────
    if remaining < 100:
        await update.message.reply_text(
            f"⚠️ **Sisa saldo Anda hampir habis ({remaining:,} Poin).**\n"
            "Harap hubungi Admin untuk top-up pengerjaan selanjutnya.",
            parse_mode="Markdown"
        )

import random
import re
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from core.config import TIER_MODELS, READY, TIER_DISPLAY_LABELS
from database import get_session
import user_service
from prompt_assembler import assemble_evaluator_prompt
from kie_api import call_ai_engine_with_cost, call_ai_engine_multimodal_with_cost, TASK_MARKUP
from utils.helpers import send_large_message, _retry_telegram_call
from utils.helpers import send_large_message, _retry_telegram_call

logger = logging.getLogger(__name__)


def _calculate_dynamic_price(tier: str, content_len: int = 2000) -> int:
    """
    Menghitung harga dinamis (randomize) berdasarkan tier dan estimasi panjang input.
    Digunakan oleh SEMUA task: PR, TC, CYU, maupun VCG (image-based).

    Ranges:
    - BASIC:   Short(<1k): 80-90,  Medium(1k-4k): 90-105,  Long(>4k): 105-120
    - PRO/PREMIUM: Short(<1k): 200-220, Medium(1k-4k): 220-240, Long(>4k): 240-250

    Args:
        tier: "BASIC", "PRO", atau "PREMIUM"
        content_len: Total panjang karakter semua input (default 2000 untuk VCG image).
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



def _build_result_ui(
    tier: str,
    price: int,
    remaining: int,
    eval_id: int,
    is_vcg: bool = False,
) -> tuple:
    """Membangun disclaimer, footer, dan reply_markup untuk hasil evaluasi.

    Dipanggil oleh _run_evaluation_background() dan _run_vcg_evaluation_background()
    untuk menghindari duplikasi kode yang identik.
    """
    tier_label = TIER_DISPLAY_LABELS.get(tier, tier)
    label = "Evaluasi VCG Selesai!" if is_vcg else "Evaluasi Selesai!"
    next_hint = "ganti task." if is_vcg else "ganti task/proyek."

    disclaimer_html = (
        "⚠️ <b>PERINGATAN</b>: <i>Tugas AI hanya membantu. Harap telaah kembali hasil evaluasi ini "
        "dengan cermat (Critical Thinking required).</i>\n"
        "──────────────────\n"
    )
    footer_html = (
        f"──────────────────\n"
        f"✅ <b>{label}</b>\n"
        f"💰 Biaya: <b>{price} Poin</b>\n"
        f"💳 Sisa Saldo: <b>{remaining:,} Poin</b>\n"
        f"──────────────────\n"
        f"💡 Ketik <b>/mulai</b> untuk lanjut, atau <b>/cancel</b> untuk {next_hint}\n"
    )

    reply_markup = None
    if eval_id:
        kb = [[
            InlineKeyboardButton("👍 Akurat", callback_data=f"feed_pos_{eval_id}"),
            InlineKeyboardButton("👎 Kurang", callback_data=f"feed_neg_{eval_id}"),
        ]]
        reply_markup = InlineKeyboardMarkup(kb)

    return disclaimer_html, footer_html, reply_markup

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
    # ── PRIORITAS: PR — Dinamis A–F (cek SEBELUM dispatch berbasis len(args)) ──
    # Harus di atas semua if len(args)==N agar PR+5/6 args tidak salah masuk branch lain.
    if task_type == "PR":
        args_list = list(args)
        user_ask = args_list[0] if args_list else ""
        responses = args_list[1:]
        payload = f"USER ASK:\n{user_ask}"
        has_any_response = False
        for i, resp in enumerate(responses):
            if resp and resp.strip():
                label = chr(65 + i)  # A, B, C, D, E, F
                payload += f"\n\nRESPONSE {label}:\n{resp}"
                has_any_response = True
        if not has_any_response:
            payload += "\n\n[Tidak ada response yang dikirim]"
        return payload

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

    if len(args) == 9 and task_type == "TA_WRITING_TOOLS_CONTEXTUAL_SYNONYMS":
        orig, a1, a2, a3, a4, b1, b2, b3, b4 = args
        return (
            f"ORIGINAL TEXT:\n{orig}\n\n"
            f"RESPONSE A1:\n{a1 or 'N/A'}\n\n"
            f"RESPONSE A2:\n{a2 or 'N/A'}\n\n"
            f"RESPONSE A3:\n{a3 or 'N/A'}\n\n"
            f"RESPONSE A4:\n{a4 or 'N/A'}\n\n"
            f"RESPONSE B1:\n{b1 or 'N/A'}\n\n"
            f"RESPONSE B2:\n{b2 or 'N/A'}\n\n"
            f"RESPONSE B3:\n{b3 or 'N/A'}\n\n"
            f"RESPONSE B4:\n{b4 or 'N/A'}"
        )

    if task_type == "AFM_SAFETY_EVALUATION_AFM4":
        user_ask = args[0]
        responses = args[1:]
        payload = f"USER ASK:\n{user_ask}"
        for i, resp in enumerate(responses):
            if resp and resp.strip():
                label = chr(65 + i)
                payload += f"\n\nRESPONSE {label}:\n{resp}"
        return payload

    # Default logic (4 args: user_ask, resp_a, resp_b, resp_c)
    args_list = list(args)
    while len(args_list) < 4:
        args_list.append("")
    user_ask, resp_a, resp_b, resp_c = args_list[:4]

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

    # ── KHUSUS: TA_INTELLIGENT_POLLS ──────────────────────────────────────
    if task_type == "TA_INTELLIGENT_POLLS":
        payload = f"[CONVERSATION]\n{user_ask}\n\n[RESPONSE A]\n{resp_a}"
        if resp_b:
            payload += f"\n\n[RESPONSE B]\n{resp_b}"
        else:
            payload += "\n\n[Response B tidak disertakan — hanya 1 response yang dievaluasi]"
        if resp_c:
            payload += f"\n\n[RESPONSE C]\n{resp_c}"
        return payload

    # ── DEFAULT: TC, AFM, CYU website, dan lainnya ───────────────────────
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

    # 0. Balance pre-check (minimum)
    async with get_session() as session:
        has_balance = await user_service.check_balance(session, tg_id, 5)
    if not has_balance:
        await status_msg.edit_text(
            "❌ Saldo tidak mencukupi (Minimum 5 Poin).\n"
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
        llm_response, price = await call_ai_engine_with_cost(
            system_prompt=evaluator_prompt, user_input=user_input_payload, markup=TASK_MARKUP, model_override=model
        )
    except Exception as e:
        logger.error(f"API call error: {e}")
        try:
            await _retry_telegram_call(
                status_msg.edit_text,
                "❌ **Sistem sibuk, saldo tidak dipotong.**\n"
                "Silakan coba lagi nanti.\n\n"
                f"Detail: `{type(e).__name__}: {e}`"
            )
        except Exception:
            pass
        return

    # Cek apakah response menunjukkan error (❌) atau peringatan sistem (⚠️)
    if llm_response.startswith(("❌", "⚠️")):
        try:
            await _retry_telegram_call(
                status_msg.edit_text,
                "❌ **Sistem sibuk, saldo tidak dipotong.**\n"
                "Silakan coba lagi nanti.\n\n"
                f"{llm_response}"
            )
        except Exception:
            pass
        return

    try:
        await _retry_telegram_call(status_msg.edit_text, "✅ Respons diterima! Memotong saldo...")
    except Exception:
        pass

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
    try:
        await _retry_telegram_call(status_msg.delete)
    except Exception as e:
        logger.warning(f"Gagal hapus status_msg: {e}")
    disclaimer_html, footer_html, reply_markup = _build_result_ui(tier, price, remaining, eval_id)

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
    # Balance pre-check (minimum)
    async with get_session() as session:
        has_balance = await user_service.check_balance(session, tg_id, 5)
    if not has_balance:
        await status_msg.edit_text(
            "❌ Saldo tidak mencukupi (Minimum 5 Poin).\nHubungi Admin untuk top-up."
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
    elif task_type == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        instruction_ref = "VCG Edit Model Direct Manipulation"
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
    elif task_type == "VCG_EDIT_MODEL_DIRECT_MANIPULATION":
        new_images_b64 = {}
        if "A" in images_b64: new_images_b64["Input Image"] = images_b64["A"]
        if "B" in images_b64: new_images_b64["Selection Mask"] = images_b64["B"]
        if "C" in images_b64: new_images_b64["Left Image"] = images_b64["C"]
        if "D" in images_b64: new_images_b64["Right Image"] = images_b64["D"]
        if "E" in images_b64: new_images_b64["Left Heatmap"] = images_b64["E"]
        if "F" in images_b64: new_images_b64["Right Heatmap"] = images_b64["F"]
        images_b64 = new_images_b64

        img_count = len(images_b64)

        labels = []
        if "Input Image" in images_b64: labels.append("Input Image")
        if "Selection Mask" in images_b64: labels.append("Selection Mask")
        if "Left Image" in images_b64: labels.append("Left Image")
        if "Right Image" in images_b64: labels.append("Right Image")
        if "Left Heatmap" in images_b64: labels.append("Left Heatmap")
        if "Right Heatmap" in images_b64: labels.append("Right Heatmap")
        img_labels_str = ", ".join(labels)
        
        user_input_text = (
            f"USER PROMPT: {user_prompt}\n\n"
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
        llm_response, price = await call_ai_engine_multimodal_with_cost(
            system_prompt=evaluator_prompt,
            user_text=user_input_text,
            images_b64=images_b64,
            markup=TASK_MARKUP,
            model_override=model,
        )
    except Exception as e:
        logger.error(f"VCG API error: {e}")
        try:
            await _retry_telegram_call(
                status_msg.edit_text,
                "❌ **Sistem sibuk, saldo tidak dipotong.**\n"
                f"Detail: `{type(e).__name__}: {e}`"
            )
        except Exception:
            pass
        return

    if llm_response.startswith(("❌", "⚠️")):
        try:
            await _retry_telegram_call(
                status_msg.edit_text,
                f"❌ **Sistem error, saldo tidak dipotong.**\n{llm_response}"
            )
        except Exception:
            pass
        return

    try:
        await _retry_telegram_call(status_msg.edit_text, "✅ Respons VCG diterima! Memotong saldo...")
    except Exception:
        pass

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

    try:
        await _retry_telegram_call(status_msg.delete)
    except Exception as e:
        logger.warning(f"[VCG] Gagal hapus status_msg: {e}")
    disclaimer_html, footer_html, reply_markup = _build_result_ui(tier, price, remaining, eval_id, is_vcg=True)

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

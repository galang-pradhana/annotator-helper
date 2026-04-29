"""
bot.py
------
Telegram Bot Orchestrator untuk Centific Annotation.
Menggunakan ConversationHandler sebagai state machine utama.
Sistem: Credit-Based Billing (Pay-per-hit).

State Flow:
  /start → SELECTING_LANG → SELECTING_TASK → SELECTING_TIER → READY → COLLECTING_* → (PROCESSING)
                                                                 ↑                        │
                                                                 └────────────────────────┘
"""

import logging
import os
import re
import random
import asyncio
import time
import base64
import html
import io

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    TypeHandler,
    ContextTypes,
    ApplicationHandlerStop,
    filters,
)
from collections import deque
from dotenv import load_dotenv

load_dotenv()

# --- Deduplication Cache ---
processed_updates = deque(maxlen=1000)
# ---------------------------

from database import init_db, get_session
import user_service
from prompt_assembler import assemble_evaluator_prompt, LANGUAGE_MAP
from kie_api import call_kie_ai_api

# ── Logging ───────────────────────────────────────────────────────────────
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler("bot_logs.txt", mode="w", encoding="utf-8"), # Hapus & buat baru tiap start
        logging.StreamHandler() # Tetap tampil di terminal
    ]
)
logger = logging.getLogger(__name__)

# Silent noisy loggers for performance
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.INFO)

# ── Admin ID ──────────────────────────────────────────────────────────────
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
MAINTENANCE_MODE = False  # Global switch for Maintenance Mode

# ── Pricing & Tier Constants ─────────────────────────────────────────────
# Dynamic Pricing Ranges (Length-based, randomized per hit):
# BASIC:   Short(<1k): 80-90,  Medium(1k-4k): 90-105,  Long(>4k): 105-120
# PRO/PREMIUM: Short(<1k): 200-220, Medium(1k-4k): 220-240, Long(>4k): 240-250
TIER_PRICING = {
    "BASIC": 99,    # Median estimasi untuk balance check awal
    "PRO": 225,     # Median estimasi untuk balance check awal
    "PREMIUM": 225, # Median estimasi untuk balance check awal
}
TIER_MODELS = {
    "BASIC": "gemini-3-flash",
    "PRO": "gemini-3.1-pro",
    "PREMIUM": "claude-sonnet-4-6",
}
# Label ramah pengguna untuk tampilan di chat (menyembunyikan nama model teknis)
TIER_DISPLAY_LABELS = {
    "BASIC": "Basic",
    "PRO": "Pro",
    "PREMIUM": "Premium",
}
TIER_DISPLAY_RANGES = {
    "BASIC": "85 - 120",
    "PRO": "200 - 250",
    "PREMIUM": "200 - 250",
}

# ── State Constants ───────────────────────────────────────────────────────
(
    SELECTING_LANG,
    SELECTING_PROJECT,
    SELECTING_TASK,
    CONFIRMING_TASK,
    SELECTING_TIER,
    READY,
    SELECTING_SUBTASK,
    SELECTING_VCG_SUBTASK,
    COLLECTING_USER_ASK,
    COLLECTING_RESP_A,
    COLLECTING_RESP_B,
    COLLECTING_RESP_C,
    # VCG-specific states (image-based input)
    COLLECTING_VCG_PROMPT,
    COLLECTING_VCG_IMAGE_A,
    COLLECTING_VCG_IMAGE_B,
    COLLECTING_VCG_IMAGE_C,
    COLLECTING_VCG_IMAGE_D,
    # Single-shot state: PSR & Writing QA (all input in one message, /next to evaluate)
    COLLECTING_SINGLE_SHOT,
) = range(18)

DEPOSIT_ASK_NOMINAL = 100


# ══════════════════════════════════════════════════════════════════════════
#  MIDDLEWARE (Group 0) — Deduplication + Basic Access Control
# ══════════════════════════════════════════════════════════════════════════

async def check_access_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Middleware yang berjalan sebelum Command/Message handler.
    Melakukan deduplication dan cek registrasi dasar.
    """
    # 0. Deduplication Cache
    if update.update_id in processed_updates:
        logger.warning(f"Duplicate update {update.update_id} ignored.")
        raise ApplicationHandlerStop()
    processed_updates.append(update.update_id)

    if not update.effective_user:
        return

    tg_id = update.effective_user.id
    is_admin = (tg_id == ADMIN_ID)

    # ── Task 8: Maintenance Mode Check ──────────────────────────────
    global MAINTENANCE_MODE
    if MAINTENANCE_MODE and not is_admin:
        if update.message:
            await update.message.reply_text(
                "🚧 **Bot Sedang Maintenance**\n\n"
                "Maaf, saat ini sedang dalam perbaikan oleh Admin. "
                "Silakan coba lagi beberapa saat lagi.",
                parse_mode="Markdown"
            )
        elif update.callback_query:
            await update.callback_query.answer(
                "🚧 Bot sedang Maintenance. Harap tunggu.", show_alert=True
            )
        raise ApplicationHandlerStop()

    # Bypass callback queries dari rate limit agar tombol tetap responsif
    if update.callback_query:
        return

    if not update.message:
        return

    text = update.message.text or ""

    # ── Task 3: Rate Limiter (5 detik) ──────────────────────────────
    if not is_admin:
        last_time = context.user_data.get("last_request_time", 0)
        now = time.time()
        if now - last_time < 5:
            wait_time = int(5 - (now - last_time))
            if text.startswith("/"):
                await update.message.reply_text(
                    f"⏳ **Terlalu Cepat!**\n"
                    f"Harap tunggu {wait_time} detik lagi.",
                    parse_mode="Markdown"
                )
            raise ApplicationHandlerStop()
        context.user_data["last_request_time"] = now

    # BYPASS: Biarkan command utama lolos
    if text.startswith(("/start", "/cancel", "/deposit", "/add_balance", "/add", "/stats", "/help", "/status", "/history", "/user", "/broadcast", "/check_fail", "/maintenance")):
        return


async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is admin."""
    return update.effective_user.id == ADMIN_ID


async def mulai_outside_ready(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Informasi ketika /mulai dipanggil di luar state READY."""
    await update.message.reply_text(
        "⚠️ **Perintah /mulai tidak bisa dijalankan sekarang.**\n\n"
        "Kemungkinan penyebab:\n"
        "• Anda belum menyelesaikan setup (pilih bahasa, proyek, task, dan tier)\n"
        "• Sesi sebelumnya sudah dibatalkan\n\n"
        "Ketik /start untuk memulai setup dari awal.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════════════════
#  CONVERSATION HANDLERS — State Machine
# ══════════════════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler Command /start — Registrasi/Sapa user + minta pilih bahasa."""
    tg_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or "User"
    
    # Reset session on /start
    context.user_data.clear()

    async with get_session() as session:
        user, is_new = await user_service.register_or_get_user(session, tg_id, username)

    if is_new:
        msg = (
            f"🎉 **Selamat Datang, {username}!**\n\n"
            f"Anda telah terdaftar di **Annotator Pro**.\n"
            f"🎁 Bonus pendaftaran: **{user.balance:,} Poin**\n\n"
            "Mari mulai setup. Silakan pilih bahasa target Anda."
        )
    else:
        msg = (
            f"👋 **Halo kembali, {username}!**\n\n"
            f"💰 Saldo Anda: **{user.balance:,} Poin**\n\n"
            "Silakan pilih bahasa target Anda."
        )

    await update.message.reply_text(msg, parse_mode="Markdown")

    # Tampilkan pilihan bahasa
    lang_keyboard = [
        [
            InlineKeyboardButton("🇯🇵 Jepang", callback_data="lang_JA"),
            InlineKeyboardButton("🇹🇭 Thailand", callback_data="lang_TH"),
        ],
        [
            InlineKeyboardButton("🇺🇸 Inggris", callback_data="lang_EN"),
            InlineKeyboardButton("🇮🇩 Indonesia", callback_data="lang_ID"),
        ],
        [
            InlineKeyboardButton("🇰🇷 Korea", callback_data="lang_KO"),
            InlineKeyboardButton("🇻🇳 Vietnam", callback_data="lang_VI"),
        ],
        [
            InlineKeyboardButton("🇲🇾 Malaysia", callback_data="lang_MS"),
            InlineKeyboardButton("🇸🇦 Arab", callback_data="lang_AR"),
        ],
    ]
    await update.message.reply_text(
        "🌐 **Langkah 1/5** — Pilih bahasa target:",
        reply_markup=InlineKeyboardMarkup(lang_keyboard),
        parse_mode="Markdown",
    )
    return SELECTING_LANG


async def back_lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang_keyboard = [
        [ InlineKeyboardButton("🇯🇵 Jepang", callback_data="lang_JA"), InlineKeyboardButton("🇹🇭 Thailand", callback_data="lang_TH") ],
        [ InlineKeyboardButton("🇺🇸 Inggris", callback_data="lang_EN"), InlineKeyboardButton("🇮🇩 Indonesia", callback_data="lang_ID") ],
        [ InlineKeyboardButton("🇰🇷 Korea", callback_data="lang_KO"), InlineKeyboardButton("🇻🇳 Vietnam", callback_data="lang_VI") ],
        [ InlineKeyboardButton("🇲🇾 Malaysia", callback_data="lang_MS"), InlineKeyboardButton("🇸🇦 Arab", callback_data="lang_AR") ],
    ]
    await query.edit_message_text(
        "🌐 **Langkah 1/5** — Pilih bahasa target:",
        reply_markup=InlineKeyboardMarkup(lang_keyboard),
        parse_mode="Markdown",
    )
    return SELECTING_LANG

async def back_proj_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    async with get_session() as session:
        projects = await user_service.get_projects(session)
    project_keyboard = []
    row = []
    for proj in projects:
        row.append(InlineKeyboardButton(proj.name, callback_data=f"proj_{proj.code}"))
        if len(row) == 2:
            project_keyboard.append(row)
            row = []
    if row: project_keyboard.append(row)
    project_keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_lang")])
    await query.edit_message_text("📂 **Langkah 2/5** — Pilih Proyek:", reply_markup=InlineKeyboardMarkup(project_keyboard), parse_mode="Markdown")
    return SELECTING_PROJECT

async def back_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    tg_id = update.effective_user.id
    async with get_session() as session:
        user = await user_service.get_user_info(session, tg_id)
        project_code = user.selected_project or "CHERRY_OPAL"
        tasks = await user_service.get_tasks_by_project(session, project_code)
    task_keyboard = []
    row = []
    for task in tasks:
        icon = "📝"
        if "AFM" in task.code: icon = "🎨"
        elif "CYU" in task.code: icon = "🌐"
        elif "VCG" in task.code: icon = "🎬"
        elif "TA" in task.code: icon = "📩"
        row.append(InlineKeyboardButton(f"{icon} {task.name}", callback_data=f"task_{task.code}"))
        if len(row) == 1:
            task_keyboard.append(row)
            row = []
    if row: task_keyboard.append(row)
    task_keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_proj")])
    await query.edit_message_text("🛠️ **Langkah 3/5** — Pilih jenis task:", reply_markup=InlineKeyboardMarkup(task_keyboard), parse_mode="Markdown")
    return SELECTING_TASK


async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Callback saat user memilih bahasa dari inline keyboard."""
    start_time = time.time()
    query = update.callback_query
    await query.answer()

    lang_code = query.data.split("_", 1)[1]  # e.g. "lang_TH" → "TH"
    tg_id = update.effective_user.id

    context.user_data["TARGET_LANGUAGE"] = lang_code

    async with get_session() as session:
        await user_service.update_language(session, tg_id, lang_code)

    lang_name = LANGUAGE_MAP.get(lang_code, ("Unknown", ""))[0]
    await query.edit_message_text(
        f"✅ Bahasa diset ke: **{lang_name}** (`{lang_code}`)\n\n"
        "Sekarang pilih proyek pengerjaan Anda.",
        parse_mode="Markdown",
    )

    # Tampilkan pemilihan proyek
    async with get_session() as session:
        projects = await user_service.get_projects(session)
    
    project_keyboard = []
    # Baris pertama untuk semua proyek
    row = []
    for proj in projects:
        row.append(InlineKeyboardButton(proj.name, callback_data=f"proj_{proj.code}"))
        if len(row) == 2:
            project_keyboard.append(row)
            row = []
    if row:
        project_keyboard.append(row)
    project_keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_lang")])

    await query.message.reply_text(
        "📂 **Langkah 2/5** — Pilih Proyek:",
        reply_markup=InlineKeyboardMarkup(project_keyboard),
        parse_mode="Markdown",
    )
    return SELECTING_PROJECT


async def project_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Callback saat user memilih proyek dari inline keyboard."""
    start_time = time.time()
    query = update.callback_query
    await query.answer()

    project_code = query.data.split("_", 1)[1]
    tg_id = update.effective_user.id

    context.user_data["SELECTED_PROJECT"] = project_code

    async with get_session() as session:
        await user_service.update_project(session, tg_id, project_code)
        tasks = await user_service.get_tasks_by_project(session, project_code)

    await query.edit_message_text(
        f"✅ Proyek diset ke: **{project_code.replace('_', ' ')}**\n\n"
        "Sekarang pilih jenis pekerjaan Anda.",
        parse_mode="Markdown",
    )

    # Tampilkan pemilihan task dari DB
    task_keyboard = []
    row = []
    for task in tasks:
        # Icon mapping or default
        icon = "📝"
        if "AFM" in task.code: icon = "🎨"
        elif "CYU" in task.code: icon = "🌐"
        elif "VCG" in task.code: icon = "🎬"
        elif "TA" in task.code: icon = "📩"
        
        row.append(InlineKeyboardButton(f"{icon} {task.name}", callback_data=f"task_{task.code}"))
        if len(row) == 1: # One per row for better readability
            task_keyboard.append(row)
            row = []
    if row:
        task_keyboard.append(row)
    task_keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_proj")])

    await query.message.reply_text(
        "🛠️ **Langkah 3/5** — Pilih jenis task:",
        reply_markup=InlineKeyboardMarkup(task_keyboard),
        parse_mode="Markdown",
    )
    logger.info(f"project_callback took {time.time() - start_time:.3f}s")
    return SELECTING_TASK


async def task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Callback saat user memilih task dari inline keyboard."""
    start_time = time.time()
    query = update.callback_query
    await query.answer()

    task_code = query.data.split("_", 1)[1]  # e.g. "task_PR" → "PR"
    tg_id = update.effective_user.id

    context.user_data["SELECTED_TASK"] = task_code

    async with get_session() as session:
        await user_service.update_task(session, tg_id, task_code)

    # JALUR KHUSUS TA_TC (Text Composition): Pilih Sub-task
    if task_code == "TA_TC":
        subtask_keyboard = [
            [InlineKeyboardButton("📩 TC Message Reply", callback_data="sub_TC_MESSAGE_REPLY")],
            [InlineKeyboardButton("✍️ TC Proofreading", callback_data="sub_TC_PROOFREADING")],
            [InlineKeyboardButton("🖋️ Writing Tool - Proofreading V2", callback_data="sub_WRITING_TOOL_PROOFREAD_V2")],
            [InlineKeyboardButton("🧠 PSR Personalized Smart Reply", callback_data="sub_TA_PERSONALIZED_SMART_REPLY")],
            [InlineKeyboardButton("📝 Writing QA", callback_data="sub_TA_WRITING_TOOLS_WRITING_QA")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_task")],
        ]
        await query.edit_message_text(
            "📩 **Langkah 3.5/5** — Pilih Sub-task Text Composition:",
            reply_markup=InlineKeyboardMarkup(subtask_keyboard),
            parse_mode="Markdown",
        )
        return SELECTING_SUBTASK

    # JALUR KHUSUS VCG (Visual Content Generation): Pilih Sub-task
    if task_code == "VCG":
        vcg_subtask_keyboard = [
            [InlineKeyboardButton("🎨 ADM - Base Creation Model", callback_data="vcgsub_VCG_ADM_BASE_CREATION")],
            [InlineKeyboardButton("🖼️ Background Message", callback_data="vcgsub_VCG_BACKGROUND_MESSAGE")],
            [InlineKeyboardButton("✏️ Edit Model", callback_data="vcgsub_VCG_EDIT_MODEL")],
            [InlineKeyboardButton("✍️ Prompt Rewrite Variety Review", callback_data="vcgsub_VCG_PROMPT_REWRITE")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_task")],
        ]
        await query.edit_message_text(
            "🎬 **Visual Content Generation (VCG)**\n\n"
            "📋 **Langkah 3.5/5** — Pilih Tipe Pekerjaan VCG:",
            reply_markup=InlineKeyboardMarkup(vcg_subtask_keyboard),
            parse_mode="Markdown",
        )
        return SELECTING_VCG_SUBTASK

    # JALUR KHUSUS CYU (Website Topic): Pilih Sub-task
    if task_code == "CYU":
        cyu_subtask_keyboard = [
            [InlineKeyboardButton("🌐 CYU Website Topic", callback_data="sub_CYU_WEBSITE_TOPIC")],
            [InlineKeyboardButton("📄 CYU Topline Summarization", callback_data="sub_CYU_TOPLINE_SUMMARIZATION")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_task")],
        ]
        await query.edit_message_text(
            "🌐 **Langkah 3.5/5** — Pilih Sub-task CYU:",
            reply_markup=InlineKeyboardMarkup(cyu_subtask_keyboard),
            parse_mode="Markdown",
        )
        return SELECTING_SUBTASK

    confirm_text, confirm_markup = _get_confirmation_ui(task_code)
    await query.edit_message_text(
        confirm_text,
        reply_markup=confirm_markup,
        parse_mode="Markdown",
    )
    logger.info(f"task_callback took {time.time() - start_time:.3f}s")
    return CONFIRMING_TASK


async def subtask_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Callback saat user memilih sub-task (khusus Text Composition / TA_TC)."""
    start_time = time.time()
    query = update.callback_query
    await query.answer()

    subtask_code = query.data[4:]  # strip "sub_" → "TC_MESSAGE_REPLY" atau "TC_PROOFREADING"
    context.user_data["SELECTED_SUBTASK"] = subtask_code

    confirm_text, confirm_markup = _get_confirmation_ui(subtask_code)
    await query.edit_message_text(
        confirm_text,
        reply_markup=confirm_markup,
        parse_mode="Markdown",
    )
    logger.info(f"subtask_callback took {time.time() - start_time:.3f}s")
    return CONFIRMING_TASK


async def vcg_subtask_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Callback saat user memilih ADM - Base Creation Model (khusus VCG)."""
    start_time = time.time()
    query = update.callback_query
    await query.answer()

    # Tentukan label tampilan berdasarkan tombol yang dipilih
    label_map = {
        "vcgsub_VCG_ADM_BASE_CREATION": "ADM - Base Creation Model",
        "vcgsub_VCG_BACKGROUND_MESSAGE": "Background Message",
        "vcgsub_VCG_EDIT_MODEL": "Edit Model",
        "vcgsub_VCG_PROMPT_REWRITE": "Prompt Rewrite Variety Review",
    }
    # Ambil label dari button text (bukan callback_data)
    btn_text = ""
    if query.message and query.message.reply_markup:
        for row in query.message.reply_markup.inline_keyboard:
            for btn in row:
                if btn.callback_data == query.data:
                    btn_text = btn.text
                    break

    vcg_subtask_code = query.data[7:]  # strip "vcgsub_"
    context.user_data["SELECTED_SUBTASK"] = vcg_subtask_code
    context.user_data["VCG_MODEL_LABEL"] = btn_text or label_map.get(query.data, vcg_subtask_code)

    confirm_text, confirm_markup = _get_confirmation_ui(vcg_subtask_code)
    await query.edit_message_text(
        confirm_text,
        reply_markup=confirm_markup,
        parse_mode="Markdown",
    )
    logger.info(f"vcg_subtask_callback took {time.time() - start_time:.3f}s")
    return CONFIRMING_TASK


def _get_confirmation_ui(task_code: str) -> tuple[str, InlineKeyboardMarkup]:
    """Helper untuk merakit teks konfirmasi berdasarkan task."""

    # Mapping pertanyaan per task
    QUESTIONS = {
        "PR": [
            "Does the response follow the user’s instructions?",
            "Are there any localization issues in the response?",
            "How concise is the response?",
            "How truthful is the response?",
            "How satisfying is the response?",
            "In terms of Satisfaction, how do these two responses compare?",
            "Please describe the reasons for your gradings (satu rangkuman utama dalam bahasa Indonesia DAN bahasa Inggris)."
        ],
        "AFM": [
            "GAQ 1a: Is the response AFM Harm-Free?",
            "GAQ 1b: Safety Taxonomy categories (jika b/c)",
            "GAQ 2a: Additional safety flags (pilih semua yang berlaku)",
            "GAQ 3: Does the response engage with the request?",
            "GAQ 4: Does the response follow instructions? (jika engage)",
            "GAQ 5a/5b/5c: Style, redirect, decline pattern (jika tidak engage)",
            "GAQ 6a/6b: Risk awareness & disclaimer (jika engage)",
            "GAQ 7: Heuristic Satisfaction Score",
            "Reasoning (Essay bahasa Inggris)",
            "Alasan pilihan (bahasa Indonesia, 1 kalimat)",
            "Justifikasi Draf Komentar (ID & EN, 1 kalimat)",
        ],
        "TC_MESSAGE_REPLY": [
            "Does the response follow user's instructions?",
            "How grounded (truthful) is the response?",
            "How comprehensive is the response?",
            "How good is the composition in the response?",
            "There are no localization issues with the response.",
            "Does the response contain any harmful information?",
            "How satisfying is the response?",
            "Comparison (Satisfaction & Harmlessness)",
            "Reasons for your gradings"
        ],
        "TC_PROOFREADING": [
            "Does the response follow user's instructions?",
            "How grounded (truthful) is the response?",
            "How comprehensive is the response?",
            "How good is the composition in the response?",
            "Localization issues check",
            "Harmful information check",
            "Satisfaction rating",
            "Comparison & Reasons"
        ],
        "CYU_WEBSITE_TOPIC": [
            "Is the website topic correctly identified?",
            "Does the response align with the guidelines?",
            "Following Instructions check",
            "Groundedness (Hallucination/Inaccuracy check)",
            "Satisfaction Rating & Pairwise Comparison"
        ],
        "CYU_TOPLINE_SUMMARIZATION": [
            "Review Original Input Text (Main idea, key points)",
            "Input Text Irregularities & Safety check",
            "Responses Safety/Harmfulness check",
            "Comprehensiveness (Most important points & conclusions)",
            "Groundedness (Hallucination/Inaccuracy check)",
            "Composition (Localization, clarity, boilerplate)",
            "Satisfaction Categorization",
            "Pairwise Comparison & Insights"
        ],
        # VCG — Visual Content Generation
        "VCG_ADM_BASE_CREATION": [
            "Safety Flags (Violent/Sexual/Offensive/Trademarked/etc.)",
            "Visual Quality Issues (contrast, blur, stretch, rotation)",
            "Text in image — Accuracy & Alignment",
            "Structural Integrity (anatomy, objects, environment)",
            "Input/Output Alignment (does image match the prompt?)",
            "Style Alignment (does image match requested style?)",
            "Essay: Overall image quality comments (in English)",
            "Comparison A↔B (Visual Quality, SI, Alignment, Style)",
            "Comparison C↔B (Visual Quality, SI, Alignment, Style)",
            "Comparison A↔C (Visual Quality, SI, Alignment, Style)",
        ],
        "VCG_BACKGROUND_MESSAGE": [
            "Subject Placement (Off-center check)",
            "Readability (Simple details check)",
            "Color Scheme (Simple colors check)",
            "Structural Integrity score",
            "Input/Output Alignment score",
            "Visual Suitability Comparison",
            "Justification (1 sentence in ID/EN)"
        ],
        "VCG_EDIT_MODEL": [
            "Serious Problems (Violent/Sexual/Trademark/etc.)",
            "Dimension 1: Edit Instruction Adherence",
            "Dimension 2: Structural Integrity",
            "Dimension 3: Consistency with original (Unedited portion)",
            "Dimension 4: Visual Quality & Integration",
            "Dimension 5: Style Alignment",
            "Dimension 6: Character Consistency",
            "General Usability evaluation"
        ],
        "VCG_PROMPT_REWRITE": [
            "Inappropriate, Sensitive, or Stereotyped? (4 images)",
            "Human(s) or anthropomorphism present? (4 images)",
            "Structural Integrity overall rating (4 images)",
            "Text-Image Alignment overall rating (4 images)",
            "Variety rating (Low/Moderate/High)",
            "Preference score: Structural Integrity",
            "Preference score: Text-Image Alignment",
            "Preference score: Variety",
            "Justification: ID reason (1 sentence)",
            "Komentar penutup (ID & EN)"
        ],
        "WRITING_TOOL_PROOFREAD_V2": [
            "Review Original Input Text & Formality Level",
            "Initial Assessment (Q1 & Q2)",
            "Evaluate Correctness (Necessary vs Unnecessary edits)",
            "Evaluate Completeness",
            "Pairwise Comparison & Justification"
        ],
        "TA_PERSONALIZED_SMART_REPLY": [
            "Review Conversation & User Profiles",
            "Categorize Input (Last topic, ended, facts, etc.)",
            "Harmfulness Assessment (A1, A2, B1, B2)",
            "Generic Quality: Groundedness & Contextual Fit",
            "Generic Quality: Conciseness & Naturalness",
            "Tone & Empathy Alignment",
            "Personalization (Style, Patterns, Likelihood)",
            "Assistant A vs B: Pairwise Comparison",
            "Overall Insights (English Essay)",
            "Alasan Pilihan & Justifikasi Draf (Indonesian)"
        ],
        "TA_WRITING_TOOLS_WRITING_QA": [
            "Part I — Categorize User Query (Type & Writing Aspect)",
            "Part II — Accuracy & Relevance (4 pertanyaan)",
            "Part II — Conciseness (3 pertanyaan)",
            "Part II — Tone & Style (5 pertanyaan)",
            "Part II — Actionability (jika Informational/Hybrid)",
            "Part II — Educational Value (3 pertanyaan)",
            "Part II — Localization Issues",
            "Grading Summary per Response (Excellent/Good/Fair/Poor)",
            "Part III — Pairwise Comparison & Observasi Keseluruhan"
        ],
    }

    # Human-friendly task display names
    TASK_DISPLAY = {
        "PR": "PR Fine Tuning",
        "AFM": "AFM — Safety Guide (Multi Modal)",
        "TA_TC": "Text Composition (TA/TC)",
        "TC_MESSAGE_REPLY": "Text Composition — TC Message Reply",
        "TC_PROOFREADING": "Text Composition — TC Proofreading",
        "CYU": "CYU Website Topic",
        "CYU_WEBSITE_TOPIC": "CYU — Website Topic",
        "CYU_TOPLINE_SUMMARIZATION": "CYU — Topline Summarization",
        "VCG": "VCG (Visual Content Generation)",
        "VCG_ADM_BASE_CREATION": "VCG — ADM - Base Creation Model",
        "VCG_BACKGROUND_MESSAGE": "VCG — Background Message",
        "VCG_EDIT_MODEL": "VCG — Edit Model",
        "VCG_PROMPT_REWRITE": "VCG — Prompt Rewrite Variety Review",
        "WRITING_TOOL_PROOFREAD_V2": "Writing Tool - Proofreading V2",
        "TA_PERSONALIZED_SMART_REPLY": "TA/TC — Personalized Smart Reply",
        "TA_WRITING_TOOLS_WRITING_QA": "TA/TC — Writing QA",
    }

    q_list = QUESTIONS.get(task_code, QUESTIONS["PR"])
    q_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(q_list)])
    display_name = TASK_DISPLAY.get(task_code, task_code.replace('_', ' '))

    confirm_text = (
        f"✅ Task diset ke: **{display_name}**\n\n"
        f"📋 **Daftar Pertanyaan Task**:\n{q_text}\n\n"
        "Apakah pertanyaan ini sudah sesuai?"
    )

    confirm_keyboard = [
        [
            InlineKeyboardButton("✅ Ya, Kerjakan Task", callback_data="confirm_YES"),
            InlineKeyboardButton("🔙 Kembali", callback_data="confirm_NO"),
        ]
    ]
    return confirm_text, InlineKeyboardMarkup(confirm_keyboard)


async def confirm_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Callback saat user mengkonfirmasi task yang dipilih."""
    start_time = time.time()
    query = update.callback_query
    await query.answer()

    action = query.data.split("_", 1)[1]

    if action == "NO":
        return await back_task_callback(update, context)

    tg_id = update.effective_user.id

    # 💎 Langkah 4/5 — Pilih Tier AI (Sekarang untuk semua User)
    tier_keyboard = [
        [
            InlineKeyboardButton("🧊 BASIC", callback_data="tier_BASIC"),
            InlineKeyboardButton("💎 PRO", callback_data="tier_PRO"),
        ],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_task")]
    ]
    await query.edit_message_text(
        "💎 **Langkah 4/5** — Pilih Tier AI:",
        reply_markup=InlineKeyboardMarkup(tier_keyboard),
        parse_mode="Markdown",
    )
    return SELECTING_TIER


async def tier_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Callback saat Admin memilih tier (BASIC/PREMIUM)."""
    start_time = time.time()
    query = update.callback_query
    await query.answer()

    tier_code = query.data.split("_", 1)[1]  # "tier_BASIC" atau "tier_PREMIUM"
    tg_id = update.effective_user.id
    context.user_data["SELECTED_TIER"] = tier_code

    async with get_session() as session:
        await user_service.update_tier(session, tg_id, tier_code)
        user = await user_service.get_user_info(session, tg_id)

    lang_code = context.user_data.get("TARGET_LANGUAGE", "ID")
    lang_name = LANGUAGE_MAP.get(lang_code, ("Unknown", ""))[0]

    # Format task name for display
    TASK_LABELS = {
        "PR": "PR Fine Tuning",
        "TA_TC": "Text Composition (TA/TC)",
        "TC_MESSAGE_REPLY": "Text Composition — TC Message Reply",
        "TC_PROOFREADING": "Text Composition — TC Proofreading",
        "CYU": "CYU Website Topic",
        "CYU_WEBSITE_TOPIC": "CYU — Website Topic",
        "CYU_TOPLINE_SUMMARIZATION": "CYU — Topline Summarization",
        "VCG": "VCG (Visual Content Generation)",
        "VCG_ADM_BASE_CREATION": "VCG — ADM - Base Creation Model",
        "VCG_BACKGROUND_MESSAGE": "VCG — Background Message",
        "VCG_EDIT_MODEL": "VCG — Edit Model",
        "AFM": "AFM — Safety Guide (Multi Modal)",
        "WRITING_TOOL_PROOFREAD_V2": "Writing Tool - Proofreading V2",
        "TA_PERSONALIZED_SMART_REPLY": "TA/TC — Personalized Smart Reply",
        "TA_WRITING_TOOLS_WRITING_QA": "TA/TC — Writing QA",
    }
    main_task = context.user_data.get("SELECTED_TASK", "PR")
    sub_task = context.user_data.get("SELECTED_SUBTASK")
    vcg_model_label = context.user_data.get("VCG_MODEL_LABEL", "")

    if sub_task:
        task_display = TASK_LABELS.get(sub_task, sub_task.replace('_', ' '))
        if vcg_model_label:
            task_display += f" ({vcg_model_label})"
    else:
        task_display = TASK_LABELS.get(main_task, main_task.replace('_', ' '))
    
    price = TIER_PRICING.get(tier_code, 99)
    balance = user.balance if user else 0

    await query.edit_message_text(
        f"✅ Tier diset ke: **{tier_code}**\n",
        parse_mode="Markdown",
    )

    await query.message.reply_text(
        f"🎯 **Langkah 5/5** — Setup selesai!\n\n"
        f"📋 Bahasa: **{lang_name}**\n"
        f"📂 Proyek: **{(user.selected_project or 'N/A').replace('_', ' ')}**\n"
        f"🛠️ Task: **{task_display}**\n"
        f"💎 Tier chosen: **{tier_code}**\n"
        f"💳 Saldo: **{balance:,} Poin**\n\n"
        "Ketik **/mulai** untuk memulai sesi evaluasi.",
        parse_mode="Markdown",
    )
    logger.info(f"tier_callback took {time.time() - start_time:.3f}s")
    return READY


async def mulai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler saat user mengetik 'Mulai' — routing ke flow text atau VCG image."""
    # Reset semua buffer
    context.user_data['temp_user_ask'] = ""
    context.user_data['temp_resp_a'] = ""
    context.user_data['temp_resp_b'] = ""
    context.user_data['temp_resp_c'] = ""
    context.user_data['vcg_image_a'] = None
    context.user_data['vcg_image_b'] = None
    context.user_data['vcg_image_c'] = None
    context.user_data['vcg_image_d'] = None
    context.user_data['temp_single_shot'] = ""

    # Balance check
    tg_id = update.effective_user.id
    tier = context.user_data.get("SELECTED_TIER", "BASIC")
    price = TIER_PRICING.get(tier, 1000)

    async with get_session() as session:
        has_balance = await user_service.check_balance(session, tg_id, price)

    if not has_balance:
        await update.message.reply_text(
            f"❌ **Saldo Tidak Cukup!**\n\n"
            f"Harga per evaluasi: **{price} Poin**\n"
            "Silakan ketik **/deposit** untuk menambah poin otomatis.\n\n"
            "Ketik /start untuk kembali ke menu.",
            parse_mode="Markdown",
        )
        return READY

    # ── Deteksi task VCG → gunakan flow IMAGE ───────────────────────────
    subtask = context.user_data.get("SELECTED_SUBTASK", "")
    main_task = context.user_data.get("SELECTED_TASK", "")
    vcg_subtasks = ["VCG_ADM_BASE_CREATION", "VCG_BACKGROUND_MESSAGE", "VCG_EDIT_MODEL"]
    is_vcg = (subtask in vcg_subtasks) or (main_task == "VCG")

    if is_vcg:
        vcg_model = context.user_data.get("VCG_MODEL_LABEL", "ADM - Base Creation Model")
        
        if subtask == "VCG_PROMPT_REWRITE":
            prompt_msg = (
                "🚀 **Sesi Evaluasi VCG Prompt Rewrite Dimulai**\n\n"
                "⚠️ **Disclaimer**: Respons AI dirancang untuk mempermudah pengerjaan task, "
                "namun tidak bersifat absolut. Gunakan sebagai referensi pembanding.\n\n"
                f"🎨 Mode: **Visual Content Generation — {vcg_model}**\n\n"
                "📝 **Langkah 1/5** — Kirim **User Prompt**:\n"
                "Contoh: `A woman holding coffee, photorealistic`\n\n"
                "Setelah mengirim prompt, ketik **/next**."
            )
        else:
            prompt_msg = (
                "🚀 **Sesi Evaluasi VCG Dimulai**\n\n"
                "⚠️ **Disclaimer**: Respons AI dirancang untuk mempermudah pengerjaan task, "
                "namun tidak bersifat absolut. Gunakan sebagai referensi pembanding.\n\n"
                f"🎨 Mode: **Visual Content Generation — {vcg_model}**\n\n"
                "📝 **Langkah 1/4** — Kirim **User Prompt** dan **Target Style**:\n"
                "Format: `[User Prompt] | [Target Style]`\n"
                "Contoh: `A woman holding coffee, photorealistic | Cinematic`\n\n"
                "Setelah mengirim prompt, ketik **/next**."
            )
            
        await update.message.reply_text(prompt_msg, parse_mode="Markdown")
        context.user_data['in_evaluation'] = True
        return COLLECTING_VCG_PROMPT

    # ── Single-Shot tasks (semua input dlm 1+ pesan, /next untuk proses)
    SINGLE_SHOT_TASKS = {
        "TA_PERSONALIZED_SMART_REPLY", 
        "TA_WRITING_TOOLS_WRITING_QA",
        "AFM"
    }

    # ── Multi-Step tasks (All-in-One didukung, atau step-by-step via /next)
    MULTI_STEP_TASKS = {
        "PR",
        "CYU_WEBSITE_TOPIC",
        "CYU_TOPLINE_SUMMARIZATION",
        "TC_MESSAGE_REPLY",
        "TC_PROOFREADING",
        "WRITING_TOOL_PROOFREAD_V2"
    }

    final_task_code = subtask or main_task
    if final_task_code in SINGLE_SHOT_TASKS or final_task_code in MULTI_STEP_TASKS:
        # Tentukan format petunjuk berdasarkan task
        disclaimer = (
            "⚠️ *Disclaimer: Respons AI hanya sebagai referensi pembanding. Tetap gunakan critical thinking.*\n"
            "🚀 **Mode All-in-One**: Jika total input < 4096 karakter, kirim semuanya sekaligus dalam satu pesan. "
            "Jika lebih panjang, kirim bertahap baru ketik **/next**.\n\n"
        )

        if final_task_code == "PR":
            task_name = "PR — Preference Ranking"
            detail = (
                "📋 **Cara Input (Pilih salah satu):**\n\n"
                "🔹 **Opsi 1: All-in-One (Cepat)**\n"
                "Jika total teks < 4096 karakter, paste semua data berikut dalam **satu pesan**:\n"
                "`User Ask: [isi]`\n"
                "`Response A: [isi]`\n"
                "`Response B: [isi]`\n"
                "`Response C: [isi — opsional]`\n"
                "Lalu ketik **/next**.\n\n"
                "🔹 **Opsi 2: Bertahap**\n"
                "Kirim **User Ask** saja dulu, lalu ketik **/next**. Bot akan memandu Anda meminta Response A, B, dst."
            )
        elif final_task_code == "TA_PERSONALIZED_SMART_REPLY":
            task_name = "PSR — Personalized Smart Reply"
            detail = (
                "📋 **Cara Input (Pilih salah satu):**\n\n"
                "🔹 **Opsi 1: All-in-One (Cepat)**\n"
                "Paste format ini dalam **satu pesan**:\n"
                "`Conversation: [isi]`\n"
                "`User Profiles: [isi]`\n"
                "`Response A1: [isi]`\n"
                "`Response B1: [isi]`\n"
                "Lalu ketik **/next**.\n\n"
                "🔹 **Opsi 2: Bertahap**\n"
                "Kirim bagian per bagian (Conversation dulu, dst), lalu ketik **/next**."
            )
        elif final_task_code == "TA_WRITING_TOOLS_WRITING_QA":
            task_name = "Writing QA"
            detail = (
                "📋 **Cara Input (Pilih salah satu):**\n\n"
                "🔹 **Opsi 1: All-in-One (Cepat)**\n"
                "Paste format ini dalam **satu pesan**:\n"
                "`Original Text: [isi]`\n"
                "`User Query: [isi]`\n"
                "`Response A: [isi]`\n"
                "`Response B: [isi]`\n"
                "Lalu ketik **/next**.\n\n"
                "🔹 **Opsi 2: Bertahap**\n"
                "Kirim bagian per bagian, lalu ketik **/next**."
            )
        elif final_task_code == "AFM":
            task_name = "AFM — Safety Guide Logic"
            detail = (
                "📋 **Cara Input (Pilih salah satu):**\n\n"
                "🔹 **Opsi 1: All-in-One**\n"
                "Paste dalam **satu pesan**:\n"
                "`User Input: [isi]`\n"
                "`Response: [isi]`\n"
                "Lalu ketik **/next**.\n\n"
                "🔹 **Opsi 2: Bertahap**\n"
                "Kirim User Input dulu, lalu Response, baru ketik **/next**."
            )
        elif "CYU" in final_task_code:
            task_name = "CYU — Website Topic / Topline"
            detail = (
                "📋 **Cara Input (Pilih salah satu):**\n\n"
                "🔹 **Opsi 1: All-in-One**\n"
                "Paste dalam **satu pesan**:\n"
                "`User: [isi]`\n"
                "`Response A: [isi]`\n"
                "`Response B: [isi]`\n"
                "Lalu ketik **/next**.\n\n"
                "🔹 **Opsi 2: Bertahap**\n"
                "Kirim **User** saja dulu, lalu ketik **/next**. Bot akan memandu Anda meminta Response A, B, dst."
            )
        elif "TC" in final_task_code or "PROOFREAD" in final_task_code:
            task_name = "TC — Message Reply / Proofreading"
            detail = (
                "📋 **Cara Input (Pilih salah satu):**\n\n"
                "🔹 **Opsi 1: All-in-One**\n"
                "Paste dalam **satu pesan**:\n"
                "`User Ask: [isi]`\n"
                "`Response A: [isi]`\n"
                "`Response B: [isi]`\n"
                "Lalu ketik **/next**.\n\n"
                "🔹 **Opsi 2: Bertahap**\n"
                "Kirim **User Ask** saja dulu, lalu ketik **/next**. Bot akan memandu Anda meminta Response A, B, dst."
            )
        else:
            task_name = "Evaluasi"
            detail = (
                "📋 **Format Input:** Kirim data evaluasi dengan label yang jelas.\n\n"
                "✅ Setelah semua bagian terkirim, ketik **/next** untuk memulai evaluasi."
            )

        msg = (
            f"🚀 **Sesi {task_name} Dimulai**\n\n"
            + disclaimer
            + detail
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        context.user_data['in_evaluation'] = True

        if final_task_code in SINGLE_SHOT_TASKS:
            return COLLECTING_SINGLE_SHOT
        else:
            return COLLECTING_USER_ASK
    else:
        # Default flow (Fine Tuning lain jika ada) — step-by-step input
        msg = (
            "🚀 **Sesi Evaluasi Dimulai**\n\n"
            "⚠️ *Disclaimer: Respons AI hanya sebagai referensi pembanding.*\n\n"
            "Bot akan memandu kamu **langkah demi langkah**.\n\n"
            "📥 **Langkah 1**: Kirim **User Ask** / **Input Utama**.\n"
            "Setelah selesai, ketik **/next**."
        )
    await update.message.reply_text(msg, parse_mode="Markdown")
    context.user_data['in_evaluation'] = True
    return COLLECTING_USER_ASK


# ══════════════════════════════════════════════════════════════════════════
#  EVALUATION PROCESSING — Background Task with Refund Logic
# ══════════════════════════════════════════════════════════════════════════

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

    # Lempar ke background task
    asyncio.create_task(
        _run_evaluation_background(
            update, tg_id, lang_code, tier, final_task, status_msg,
            *args,
        )
    )

    context.user_data['in_evaluation'] = False
    return READY


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
        llm_response = await call_kie_ai_api(
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


# ══════════════════════════════════════════════════════════════════════════
#  INPUT COLLECTORS — Multi-step data gathering
# ══════════════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════════════
#  SINGLE-SHOT COLLECTOR — PSR & Writing QA (kirim bertahap, /next evaluasi)
# ══════════════════════════════════════════════════════════════════════════

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

    # Parser gagal — informasikan field yang mungkin kurang
    await update.message.reply_text(
        "⚠️ **Format tidak dikenali.** Pastikan input menggunakan label yang benar, contoh:\n\n"
        "Untuk PSR:\n"
        "`Conversation:` / `User Profiles:` / `Response A1:` / `Response B1:`\n\n"
        "Untuk Writing QA:\n"
        "`Original Text:` / `User Query:` / `Response A:`\n\n"
        f"📦 Data terkumpul saat ini: *{len(buf)} karakter*\n"
        "Kirim data tambahan atau perbaiki format, lalu ketik **/next** lagi.",
        parse_mode="Markdown",
    )
    return COLLECTING_SINGLE_SHOT


async def next_to_resp_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data.get('temp_user_ask'):
        await update.message.reply_text(
            "❌ Anda belum mengirim User Ask. Silakan kirim teksnya dulu."
        )
        return COLLECTING_USER_ASK

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

    await update.message.reply_text(
        "📥 **Langkah 3/4**: Kirim **Response B**.\n"
        "Setelah selesai, ketik **/next**.",
        parse_mode="Markdown",
    )
    return COLLECTING_RESP_B


async def collect_resp_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data['temp_resp_b'] = (
        context.user_data.get('temp_resp_b', "") + "\n" + text
    ).strip()
    return COLLECTING_RESP_B


async def next_to_resp_c(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data.get('temp_resp_b'):
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


# ══════════════════════════════════════════════════════════════════════════
#  VCG IMAGE COLLECTORS — Flow khusus untuk task Visual Content Generation
# ══════════════════════════════════════════════════════════════════════════

async def collect_vcg_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima User Prompt + Target Style untuk VCG."""
    text = update.message.text or ""
    context.user_data['temp_user_ask'] = (
        context.user_data.get('temp_user_ask', "") + "\n" + text
    ).strip()
    await update.message.reply_text(
        "✅ Prompt diterima. Ketik **/next** untuk lanjut kirim Gambar A.",
        parse_mode="Markdown",
    )
    return COLLECTING_VCG_PROMPT


async def vcg_next_to_image_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Transisi: Prompt → Gambar A."""
    if not context.user_data.get('temp_user_ask'):
        await update.message.reply_text(
            "❌ Prompt belum dikirim. Kirim **User Prompt** dulu.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_PROMPT
    await update.message.reply_text(
        "🖼️ **Langkah 2/4** — Kirim **Gambar A** (foto/image).",
        parse_mode="Markdown",
    )
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
    await update.message.reply_text(
        "✅ **Gambar A** diterima!\n"
        "Ketik **/next** untuk lanjut kirim Gambar B.",
        parse_mode="Markdown",
    )
    return COLLECTING_VCG_IMAGE_A


async def vcg_next_to_image_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Transisi: Gambar A → Gambar B."""
    if not context.user_data.get('vcg_image_a'):
        await update.message.reply_text(
            "❌ Gambar A belum dikirim. Kirim gambarnya dulu.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_A
    await update.message.reply_text(
        "🖼️ **Langkah 3/4** — Kirim **Gambar B** (foto/image).",
        parse_mode="Markdown",
    )
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
    await update.message.reply_text(
        "✅ **Gambar B** diterima!\n"
        "Ketik **/next** untuk lanjut kirim Gambar C.",
        parse_mode="Markdown",
    )
    return COLLECTING_VCG_IMAGE_B


async def vcg_next_to_image_c(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Transisi: Gambar B → Gambar C."""
    if not context.user_data.get('vcg_image_b'):
        await update.message.reply_text(
            "❌ Gambar B belum dikirim. Kirim gambarnya dulu.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_B
    subtask = context.user_data.get("SELECTED_SUBTASK", "")
    if subtask == "VCG_PROMPT_REWRITE":
        msg = "🖼️ **Langkah 4/5** — Kirim **Gambar C** (foto/image)."
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
    if subtask == "VCG_PROMPT_REWRITE":
        await update.message.reply_text(
            "✅ **Gambar C** diterima!\n"
            "Ketik **/next** untuk lanjut kirim Gambar D.",
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
    """Transisi: Gambar C → Proses (Default) atau Gambar D (Prompt Rewrite)."""
    subtask = context.user_data.get("SELECTED_SUBTASK", "")
    if subtask == "VCG_PROMPT_REWRITE":
        return await vcg_next_to_image_d(update, context)
    else:
        return await process_vcg_images(update, context)


async def vcg_next_to_image_d(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Transisi: Gambar C → Gambar D (Khusus Prompt Rewrite)."""
    if not context.user_data.get('vcg_image_c'):
        await update.message.reply_text(
            "❌ Gambar C belum dikirim. Kirim gambarnya dulu.",
            parse_mode="Markdown",
        )
        return COLLECTING_VCG_IMAGE_C
    await update.message.reply_text(
        "🖼️ **Langkah 5/5** — Kirim **Gambar D** (foto/image).",
        parse_mode="Markdown",
    )
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
    await update.message.reply_text(
        "✅ **Gambar D** diterima!\n"
        "Ketik **/next** untuk memulai evaluasi.",
        parse_mode="Markdown",
    )
    return COLLECTING_VCG_IMAGE_D


async def process_vcg_images(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Final step VCG: download gambar dari Telegram dan jalankan evaluasi multimodal."""
    file_id_a = context.user_data.get('vcg_image_a')
    file_id_b = context.user_data.get('vcg_image_b')
    file_id_c = context.user_data.get('vcg_image_c')
    file_id_d = context.user_data.get('vcg_image_d')
    user_prompt = context.user_data.get('temp_user_ask', '')

    if not user_prompt:
        await update.message.reply_text(
            "❌ User Prompt belum diisi. Ketik /cancel dan mulai ulang."
        )
        return READY

    if not file_id_a or not file_id_b:
        await update.message.reply_text(
            "❌ Minimal Gambar A dan Gambar B harus dikirim."
        )
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
        items = [("A", file_id_a), ("B", file_id_b), ("C", file_id_c), ("D", file_id_d)]
        for label, fid in items:
            if fid:
                tg_file = await bot_instance.get_file(fid)
                img_bytes = await tg_file.download_as_bytearray()
                import base64
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

    # Lempar ke background task
    asyncio.create_task(
        _run_vcg_evaluation_background(
            update, tg_id, lang_code, tier, final_task, status_msg,
            user_prompt, images_b64,
        )
    )
    context.user_data['in_evaluation'] = False
    return READY


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
    img_count = len(images_b64)
    img_labels = ", ".join(f"Gambar {k}" for k in images_b64.keys())
    
    if task_type == "VCG_PROMPT_REWRITE":
        instruction_ref = "VCG Prompt Rewrite Variety Review"
    else:
        instruction_ref = "VCG Base Creation & Edit Model"

    user_input_text = (
        f"USER PROMPT: {user_prompt}\n\n"
        f"GAMBAR YANG DIEVALUASI: {img_labels} ({img_count} gambar)\n\n"
        f"Lakukan evaluasi lengkap sesuai guideline {instruction_ref}."
    )

    await status_msg.edit_text(
        "⏳ Memproses evaluasi VCG...\n"
        f"✅ Evaluator prompt dirakit ({len(evaluator_prompt):,} karakter)\n"
        f"🖼️ Mengirim {img_count} gambar ke AI..."
    )

    # Panggil API multimodal
    try:
        llm_response = await call_kie_ai_api_multimodal(
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


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler /cancel — keluar dari conversation."""
    await update.message.reply_text(
        "👋 Sesi dibatalkan.\n"
        "Ketik /start kapan saja untuk memulai kembali."
    )
    context.user_data.clear()
    return ConversationHandler.END


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User: /history — Lihat 5 pengerjaan terakhir."""
    tg_id = update.effective_user.id
    async with get_session() as session:
        history = await user_service.get_user_history(session, tg_id)
    
    if not history:
        await update.message.reply_text("📭 Anda belum memiliki riwayat pengerjaan.")
        return

    text = "📜 **5 Riwayat Pengerjaan Terakhir Anda:**\n\n"
    kb = []
    for i, eval_obj in enumerate(history):
        date_str = eval_obj.timestamp.strftime("%d/%m %H:%M")
        task_label = eval_obj.task_code.replace("_", " ")
        text += f"{i+1}. **{task_label}** ({date_str})\n"
        kb.append([InlineKeyboardButton(f"Lihat #{i+1} - {task_label}", callback_data=f"hist_view_{eval_obj.id}")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


async def view_history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler klik item history."""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split("_")
    eval_id = int(data_parts[-1])
    
    async with get_session() as session:
        eval_obj = await user_service.get_eval_by_id(session, eval_id)
    
    if not eval_obj:
        await query.message.reply_text("❌ Data tidak ditemukan.")
        return

    date_str = eval_obj.timestamp.strftime("%Y-%m-%d %H:%M")
    
    header_html = (
        f"📅 <b>Waktu</b>: {date_str}\n"
        f"📋 <b>Task</b>: {eval_obj.task_code}\n"
        f"──────────────────\n"
        f"❓ <b>User Input</b>:\n"
        f"<code>{html.escape(eval_obj.user_input[:1000])}</code>\n"
        f"──────────────────\n"
        f"🤖 <b>Jawaban AI</b>:\n"
    )
    
    await send_large_message(
        update, 
        eval_obj.ai_output, 
        disclaimer=header_html
    )


async def feedback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler button 👍 / 👎."""
    query = update.callback_query
    # Format: feed_pos_ID atau feed_neg_ID
    parts = query.data.split("_")
    if len(parts) < 3: return
    
    action = parts[1] # pos / neg
    eval_id = int(parts[2])
    
    feedback_str = "positive" if action == "pos" else "negative"
    async with get_session() as session:
        success = await user_service.update_evaluation_feedback(session, eval_id, feedback_str)
    
    if success:
        icon = "✅" if action == "pos" else "❌"
        msg = "Feedback berhasil dicatat. Terima kasih!"
        await query.answer(f"{icon} {msg}")
        # Ubah tombol menjadi teks agar tidak diklik dua kali
        updated_text = "Terima kasih atas feedback Anda!"
        await query.edit_message_reply_markup(reply_markup=None)
    else:
        await query.answer("⚠️ Gagal mencatat feedback.")


# ══════════════════════════════════════════════════════════════════════════
#  ADMIN COMMANDS — /deposit, /stats, /broadcast, /check_fail, /user, /maintenance
# ══════════════════════════════════════════════════════════════════════════

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /broadcast <pesan> — Kirim pesan ke semua user."""
    if update.effective_user.id != ADMIN_ID: return
    
    msg_text = " ".join(context.args)
    if not msg_text:
        await update.message.reply_text("📖 Gunakan: `/broadcast <pesan>`")
        return
    
    async with get_session() as session:
        user_ids = await user_service.get_all_user_ids(session)
    
    count = 0
    status_msg = await update.message.reply_text(f"⏳ Mengirim pesan ke {len(user_ids)} user...")
    
    for uid in user_ids:
        try:
            await context.bot.send_message(
                chat_id=uid, 
                text=f"📢 **PENGUMUMAN ADMIN**\n\n{msg_text}", 
                parse_mode="Markdown"
            )
            count += 1
            await asyncio.sleep(0.05) # Jeda agar tidak kena rate limit API Telegram
        except Exception:
            continue
            
    await status_msg.edit_text(f"✅ Berhasil mengirim pesan ke {count} user.")


async def check_fail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /check_fail — Lihat 5 evaluasi negatif terakhir."""
    if update.effective_user.id != ADMIN_ID: return
    
    async with get_session() as session:
        fails = await user_service.get_recent_fails(session)
    
    if not fails:
        await update.message.reply_text("✅ Tidak ada laporan pengerjaan negatif baru.")
        return
    
    for i, f in enumerate(fails):
        text = (
            f"🚩 **Laporan Evaluasi Kurang (#{i+1})**\n"
            f"👤 User: `{f.user_id}`\n"
            f"📅 Waktu: {f.timestamp.strftime('%Y-%m-%d %H:%M')}\n"
            f"📋 Task: `{f.task_code}`\n\n"
            f"❓ Input: `{f.user_input[:200]}...`\n\n"
            f"🤖 Output: `{f.ai_output[:500]}...`"
        )
        await update.message.reply_text(text, parse_mode="Markdown")


async def user_inspector_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /user <id> — Cek profil user."""
    if update.effective_user.id != ADMIN_ID: return
    
    if not context.args:
        await update.message.reply_text("📖 Gunakan: `/user <user_id>`")
        return
        
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID harus angka.")
        return
        
    async with get_session() as session:
        user = await user_service.get_user_info(session, user_id)
    
    if not user:
        await update.message.reply_text("❌ User tidak ditemukan.")
        return
        
    text = (
        f"👤 **User Inspector**\n"
        f"🆔 ID: `{user.user_id}`\n"
        f"👤 Username: `@{user.username}`\n"
        f"💰 Saldo: **{user.balance:,} Poin**\n"
        f"🌍 Lang: `{user.selected_lang}`\n"
        f"🏗️ Project: `{user.selected_project}`\n"
        f"📋 Task: `{user.selected_task}`\n"
        f"💎 Tier: `{user.selected_tier}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def toggle_maintenance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /maintenance <on/off> — Aktifkan/Matikan Mode Perbaikan."""
    if update.effective_user.id != ADMIN_ID: return
    
    global MAINTENANCE_MODE
    args = context.args
    
    if not args:
        # Jika tanpa argumen, ubah fungsinya menjadi sekadar melihat status (atau sekalian toggle juga boleh)
        # Tapi yang lebih jelas, kita atur defaultnya hanya memberi info status saat ini.
        status_sekarang = "AKTIF 🚧" if MAINTENANCE_MODE else "NON-AKTIF ✅"
        await update.message.reply_text(
            f"ℹ️ **Status Maintenance Mode saat ini: {status_sekarang}**\n\n"
            "Gunakan perintah berikut untuk mengubahnya:\n"
            "`/maintenance on` — Untuk mengaktifkan mode pemeliharaan.\n"
            "`/maintenance off` — Untuk menonaktifkan dan membuka kembali akses user.",
            parse_mode="Markdown"
        )
        return

    command = args[0].lower()
    
    if command == "on":
        MAINTENANCE_MODE = True
        await update.message.reply_text("🚧 **Maintenance Mode diaktifkan.** User biasa tidak dapat mengakses bot.", parse_mode="Markdown")
    elif command == "off":
        MAINTENANCE_MODE = False
        await update.message.reply_text("✅ **Maintenance Mode dinonaktifkan.** Bot kini dapat diakses kembali oleh seluruh user.", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Argumen tidak dikenal. Gunakan `on` atau `off`.")


async def add_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /add_balance <user_id> <amount> — Top-up saldo user."""
    tg_id = update.effective_user.id
    logger.info(f"Add balance command received from {tg_id}. ADMIN_ID defined as: {ADMIN_ID}")
    
    if tg_id != ADMIN_ID:
        await update.message.reply_text("❌ Anda tidak memiliki akses admin.")
        return

    args = list(context.args) if context.args else []
    
    # Handle the case where user types `/add balance <id> <amount>`
    if args and args[0].lower() == "balance":
        args = args[1:]

    if not args or len(args) < 2:
        await update.message.reply_text(
            "📖 **Penggunaan**: `/add_balance <user_id> <amount_poin>`\n"
            "Contoh: `/add_balance 123456789 5000`\n\n"
            "💡 *Catatan Admin: Jika user transfer dana Rp50.000, artinya saldo yang diisi adalah 5000 Poin (Dana dibagi 10).*.",
            parse_mode="Markdown",
        )
        return

    try:
        target_user_id = int(args[0])
        amount = int(args[1])
        if amount <= 0:
            raise ValueError("Amount harus positif")
    except ValueError as e:
        await update.message.reply_text(f"❌ Input tidak valid: {e}")
        return

    try:
        async with get_session() as session:
            new_balance = await user_service.deposit_balance(
                session, target_user_id, amount
            )
        await update.message.reply_text(
            f"✅ **Berhasil!** Saldo user `{target_user_id}` bertambah **{amount:,} Poin**. Total saldo sekarang: **{new_balance:,} Poin**.",
            parse_mode="Markdown",
        )
        
        # Kirim notifikasi otomatis ke user
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🔔 Saldo Masuk! Akun Anda telah diisi sebesar {amount:,} Poin. Selamat bekerja!"
            )
        except Exception as e:
            logger.error(f"Gagal kirim notifikasi ke user {target_user_id}: {e}")
            await update.message.reply_text(f"⚠️ Notifikasi gagal dikirim ke user: {e}")

    except ValueError as e:
        await update.message.reply_text(f"❌ {e}")
    except Exception as e:
        logger.error(f"Deposit error: {e}")
        await update.message.reply_text(f"❌ Gagal deposit: {e}")

async def user_deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('in_evaluation', False):
        await update.message.reply_text("❌ Anda sedang dalam proses evaluasi. Tolong selesaikan atau ketik /cancel dulu.")
        return ConversationHandler.END
    await update.message.reply_text("💎 Berapa nominal yang ingin didepositkan? (Ketik angkanya saja, misal: 50000)")
    return DEPOSIT_ASK_NOMINAL

async def user_deposit_nominal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Mohon masukkan angka yang valid.")
        return DEPOSIT_ASK_NOMINAL
        
    nominal = int(text)
    
    rand_3 = random.randint(100, 999)
    # Gunakan 3 digit unik di belakang untuk kemudahan verifikasi admin
    if nominal >= 1000:
        base_nominal = (nominal // 1000) * 1000
        final_nominal = base_nominal + rand_3
    else:
        final_nominal = nominal + rand_3
    
    tg_id = update.effective_user.id
    
    msg = (
        "> \"💎 TOP-UP SALDO ANNOTATOR HELPER 💎\n\n"
        "Silakan lakukan transfer ke rekening berikut:\n"
        "🏦 Bank : BCA\n"
        "🔢 No. Rekening: 0481515342\n"
        "👤 A/N: Galang Putra Pradhana\n\n"
        f"Total Transfer: *Rp{final_nominal:,}*\n\n"
        f"Setelah transfer, kirimkan bukti transfer ke Admin: @Clinkzzz 🐾 dengan menyertakan ID Anda: `{tg_id}`.\n"
        "Saldo akan diproses maksimal 1x24 jam.\""
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    return ConversationHandler.END


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /stats — Lihat statistik keseluruhan."""
    tg_id = update.effective_user.id
    logger.info(f"Stats command received from {tg_id}. ADMIN_ID defined as: {ADMIN_ID}")

    if tg_id != ADMIN_ID:
        await update.message.reply_text("❌ Anda tidak memiliki akses admin.")
        return

    async with get_session() as session:
        stats = await user_service.get_stats(session)

    await update.message.reply_text(
        "📊 **Admin Stats**\n\n"
        f"👥 Total Users: **{stats['total_users']}**\n"
        f"💰 Total Poin Semua User: **{stats['total_balance']:,} Poin**\n"
        f"🎯 Hits Hari Ini: **{stats['hits_today']}**",
        parse_mode="Markdown",
    )


# ══════════════════════════════════════════════════════════════════════════
#  STANDALONE HANDLERS (Group 2) — /status, /help
# ══════════════════════════════════════════════════════════════════════════

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler Command /status — menampilkan info akun."""
    tg_id = update.effective_user.id

    async with get_session() as session:
        user = await user_service.get_user_info(session, tg_id)
        if not user:
            await update.message.reply_text(
                "Data user tidak ditemukan. Ketik /start untuk mendaftar."
            )
            return

    tier = user.selected_tier or "BASIC"
    tier_label = TIER_DISPLAY_LABELS.get(tier, "Basic")
    price_range = TIER_DISPLAY_RANGES.get(tier, "85 - 120")
    pro_info = TIER_DISPLAY_RANGES.get("PRO", "200 - 250")

    status_text = (
        "📊 **Status Akun Anda**\n\n"
        f"👤 User ID: `{tg_id}`\n"
        f"🏷️ Username: `{user.username}`\n"
        f"💰 Saldo: **{user.balance:,} Poin**\n"
        f"🌍 Bahasa: `{user.selected_lang}`\n"
        f"📂 Proyek: `{user.selected_project}`\n"
        f"🛠️ Task: `{user.selected_task}`\n"
        f"🤖 AI Tier: **{tier_label}** ({price_range} Poin/hit)\n"
        f"💎 AI Tier: Pro **({pro_info} Poin/hit)**"
    )

    await update.message.reply_text(status_text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler Command /help — panduan penggunaan."""
    tg_id = update.effective_user.id
    
    help_text = (
        "🤖 **PANDUAN LENGKAP ANNOTATOR PRO** 🤖\n\n"
        "**📂 DAFTAR TASK YANG TERSEDIA:**\n"
        "📝 **PR** (Fine Tuning)\n"
        "🎨 **AFM** (Multi Modal)\n"
        "🌐 **CYU** (Website Topic & Topline Summarization)\n"
        "🎬 **VCG** (Base Creation, Background Message, Edit Model, Prompt Rewrite)\n"
        "📩 **TC** (Message Reply & Proofreading)\n\n"
        "**👤 COMMAND UTAMA USER:**\n"
        "▫️ **/start** — Memulai setup evaluasi.\n"
        "▫️ **/deposit** — Instruksi panduan top-up saldo Poin.\n"
        "▫️ **/status** — Cek tier, proyek aktif, & saldo.\n"
        "▫️ **/history** — Lihat hasil 5 pengerjaan terakhir.\n"
        "▫️ **/help** — Membaca panduan ini.\n\n"
        "**⚙️ COMMAND SAAT EVALUASI AKTIF:**\n"
        "▫️ **/mulai** — Menjalankan sesi input evaluasi.\n"
        "▫️ **/next** — Lanjut memproses input ke langkah berikutnya.\n"
        "▫️ **/skip** — Melewati tahapan input opsional.\n"
        "▫️ **/cancel** — Membatalkan prosedur aktif saat ini."
    )
    
    if tg_id == ADMIN_ID:
        help_text += (
            "\n\n**🛠️ COMMAND ADMIN EKSKLUSIF:**\n"
            "▫️ **/add_balance** atau **/add** `<user_id> <poin>` — Top-up manual.\n"
            "▫️ **/user** `<user_id>` — Inspeksi data akun spesifik.\n"
            "▫️ **/stats** — Pantau statistik global bot.\n"
            "▫️ **/broadcast** `<pesan>` — Pengumuman massal.\n"
            "▫️ **/check_fail** — Laporan rekam riwayat failure/negative.\n"
            "▫️ **/maintenance** `<on/off>` — Toggle mode perbaikan."
        )

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command yang tidak dikenali."""
    await update.message.reply_text(
        "❓ Maaf, perintah tersebut tidak dikenali.\n"
        "Gunakan /help untuk melihat daftar perintah yang tersedia."
    )


# ══════════════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS — Parsing & Splitting
# ══════════════════════════════════════════════════════════════════════════

def _parse_evaluation_input(text: str) -> tuple[str, str, str, str] | None:
    """
    Parse input evaluasi dari user.

    Mendukung 2 format:
    1. Format terstruktur dengan separator '---':
       User Ask: ...
       ---
       Response A: ...
       ---
       Response B: ...
       ---
       Response C: ... (opsional)

    2. Format label saja (tanpa ---):
       User Ask: ...
       Response A: ...
       Response B: ...
       Response C: ... (opsional)
    """
    # ── KHUSUS: TA_PERSONALIZED_SMART_REPLY (PSR) ──────────────────
    # Task ini butuh 6 input: Conversation, User Profiles, A1, A2, B1, B2
    # Regex dibuat fleksibel terhadap spasi, baris baru, dan titik dua (:)
    psr_patterns = {
        "conv": r"(?i)(?:Conversation\s*:?\s*)([\s\S]*?)(?=(?:User\s*Profiles\s*:?)|$)",
        "prof": r"(?i)(?:User\s*Profiles\s*:?\s*)([\s\S]*?)(?=(?:Response\s*A1\s*:?)|$)",
        "a1":   r"(?i)(?:Response\s*A1\s*:?\s*)([\s\S]*?)(?=(?:Response\s*A2\s*:?)|$)",
        "a2":   r"(?i)(?:Response\s*A2\s*:?\s*)([\s\S]*?)(?=(?:Response\s*B1\s*:?)|$)",
        "b1":   r"(?i)(?:Response\s*B1\s*:?\s*)([\s\S]*?)(?=(?:Response\s*B2\s*:?)|$)",
        "b2":   r"(?i)(?:Response\s*B2\s*:?\s*)([\s\S]*?)$",
    }
    
    conv = _regex_extract(text, psr_patterns["conv"])
    prof = _regex_extract(text, psr_patterns["prof"])
    a1 = _regex_extract(text, psr_patterns["a1"])
    a2 = _regex_extract(text, psr_patterns["a2"])
    b1 = _regex_extract(text, psr_patterns["b1"])
    b2 = _regex_extract(text, psr_patterns["b2"])

    if conv and prof and (a1 or b1): # Minimal ada salah satu response
        return (conv, prof, a1, a2, b1, b2)

    # ── KHUSUS: TA_WRITING_TOOLS_WRITING_QA ────────────────────────
    # Input: Original Text, Selected Text, User Query, Response A, B, C (opsional)
    wqa_patterns = {
        "original": r"(?i)(?:Original\s*Text\s*:?\s*)([\s\S]*?)(?=(?:(?:User\s*)?Selected\s*Text\s*:?)|(?:User\s*Query\s*:?)|$)",
        "selected": r"(?i)(?:(?:User\s*)?Selected\s*Text\s*:?\s*)([\s\S]*?)(?=(?:User\s*Query\s*:?)|$)",
        "query":    r"(?i)(?:User\s*Query\s*:?\s*)([\s\S]*?)(?=(?:Response\s*A\s*:?)|$)",
        "resp_a":   r"(?i)(?:Response\s*A\s*:?\s*)([\s\S]*?)(?=(?:Response\s*B\s*:?)|$)",
        "resp_b":   r"(?i)(?:Response\s*B\s*:?\s*)([\s\S]*?)(?=(?:Response\s*C\s*:?)|$)",
        "resp_c":   r"(?i)(?:Response\s*C\s*:?\s*)([\s\S]*?)$",
    }

    wqa_original  = _regex_extract(text, wqa_patterns["original"])
    wqa_selected  = _regex_extract(text, wqa_patterns["selected"])
    wqa_query     = _regex_extract(text, wqa_patterns["query"])
    wqa_resp_a    = _regex_extract(text, wqa_patterns["resp_a"])
    wqa_resp_b    = _regex_extract(text, wqa_patterns["resp_b"])
    wqa_resp_c    = _regex_extract(text, wqa_patterns["resp_c"])

    # Valid jika ada original text, query, dan minimal satu response
    if wqa_original and wqa_query and wqa_resp_a:
        return (wqa_original, wqa_selected, wqa_query, wqa_resp_a, wqa_resp_b, wqa_resp_c)

    # ── DEFAULT: PR, TC, CYU, AFM ──────────────────────────────────────
    # Coba format 1: split by separator ---
    if "---" in text:
        sections = [s.strip() for s in text.split("---")]
        if len(sections) >= 2: # Minimal 2 section (Input + Resp)
            # Detect label di section pertama
            first_sec = sections[0]
            if re.match(r"^\s*(?:User\s*Input|Original\s*Input\s*Text|Original\s*Text|User\s*Ask|User)\s*:", first_sec, re.IGNORECASE):
                user_ask = re.sub(r"^\s*(?:User\s*Input|Original\s*Input\s*Text|Original\s*Text|User\s*Ask|User)\s*:\s*", "", first_sec, flags=re.IGNORECASE).strip()
            else:
                user_ask = first_sec # Fallback jika tidak ada label tapi ada separator

            resp_a = _strip_label(sections[1], "Response A")
            if not resp_a:
                resp_a = _strip_label(sections[1], "Response")
            
            resp_b = _strip_label(sections[2], "Response B") if len(sections) >= 3 else ""
            resp_c = _strip_label(sections[3], "Response C") if len(sections) >= 4 else ""
            
            if user_ask and resp_a:
                return (user_ask, resp_a, resp_b, resp_c)

    # Coba format 2: regex-based extraction
    patterns = {
        "user_ask": r"(?i)(?:(?:User\s*Ask|Original\s*(?:Input\s*)?Text|User\s*Input|User)\s*:\s*)([\s\S]*?)(?=Response\s*(?:A|:)|$)",
        "resp_a": r"(?i)(?:Response\s*(?:A\s*)?:\s*)([\s\S]*?)(?=Response\s*B\s*:|$)",
        "resp_b": r"(?i)(?:Response\s*B\s*:\s*)([\s\S]*?)(?=Response\s*C\s*:|$)",
        "resp_c": r"(?i)(?:Response\s*C\s*:\s*)([\s\S]*?)$",
    }

    user_ask = _regex_extract(text, patterns["user_ask"])
    resp_a = _regex_extract(text, patterns["resp_a"])
    resp_b = _regex_extract(text, patterns["resp_b"])
    resp_c = _regex_extract(text, patterns["resp_c"])

    if user_ask and resp_a:
        return (user_ask, resp_a, resp_b, resp_c)

    return None


def _strip_label(text: str, label: str) -> str:
    """Hapus label prefix seperti 'User Ask:', 'Response A:', dll."""
    pattern = re.compile(rf"^\s*{re.escape(label)}\s*:\s*", re.IGNORECASE)
    return pattern.sub("", text).strip()


def _regex_extract(text: str, pattern: str) -> str:
    """Extract content dari regex pattern."""
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


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
    # Berlaku juga untuk AFM (user_ask=Input, resp_a=Response)
    user_ask, resp_a, resp_b, resp_c = args[:4]
    payload = (
        f"USER ASK:\n{user_ask}\n\n"
        f"RESPONSE A:\n{resp_a}\n\n"
        f"RESPONSE B:\n{resp_b}"
    )
    if resp_c:
        payload += f"\n\nRESPONSE C:\n{resp_c}"
    else:
        payload += "\n\n(Response C tidak disertakan — proses dengan 2 response saja)"

    return payload


def is_balance_sufficient(current_balance: int, price: int) -> bool:
    """Cek apakah saldo mencukupi untuk harga tertentu."""
    return current_balance >= price


def _split_message(text: str, max_len: int = 3000) -> list[str]:
    """Split pesan panjang menjadi chunks yang aman untuk Telegram."""
    if len(text) <= max_len:
        return [text] if text.strip() else []

    chunks = []
    while text:
        if len(text) <= max_len:
            if text.strip():
                chunks.append(text)
            break

        split_point = text.rfind("\n", 0, max_len)
        # Jika tidak ada newline, atau newline tepat di awal (menghasilkan chunk kosong)
        if split_point <= 0:
            split_point = max_len

        chunk = text[:split_point]
        if chunk.strip():
            chunks.append(chunk)
            
        text = text[split_point:].lstrip("\n")

    return chunks


async def send_large_message(
    update: Update,
    text: str,
    disclaimer: str = "",
    footer: str = "",
    reply_markup: InlineKeyboardMarkup = None,
) -> None:
    """
    Mengirim pesan panjang ke user dengan cara:
    1. Konversi ke HTML untuk kestabilan parsing.
    2. Potong menjadi chunks jika > 4000 karakter.
    3. Jika lebih dari 2 chunks, kirim juga file .txt sebagai backup lengkap.
    4. Handle rate-limiting dan markdown errors secara otomatis.
    """
    # 1. Persiapan konten (Escape HTML untuk keamanan, kecuali tag dasar yang kita inginkan)
    # Karena LLM sering menghasilkan karakter < > yang merusak HTML, kita escape dulu.
    # Tapi kita ingin mengizinkan <b>, <i>, <code>, <a>, <pre>.
    
    def safe_html(t: str) -> str:
        """
        Mengonversi markdown sederhana ke HTML Telegram secara aman.
        """
        import re
        if not t:
            return ""
        # 1. Escape entities
        t = html.escape(t)
        # 2. Bold (mendukung multiline)
        t = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', t, flags=re.DOTALL)
        # 3. Monospace
        t = re.sub(r'`(.*?)`', r'<code>\1</code>', t)
        # 4. Bullet points
        t = re.sub(r'(?m)^\* ', r'• ', t)
        return t

    # Gunakan effective_message agar lebih aman di berbagai konteks (callback/message)
    msg_handle = update.effective_message if update.effective_message else update.message
    if not msg_handle:
        logger.error("Tidak dapat menemukan message handle untuk mengirim respons.")
        return

    # 2. Cek panjang total
    content_html = safe_html(text)
    
    full_html = ""
    if disclaimer:
        full_html += disclaimer + "\n"
    full_html += content_html
    if footer:
        full_html += "\n" + footer

    if len(full_html) <= 4000:
        try:
            await msg_handle.reply_text(full_html, parse_mode="HTML", reply_markup=reply_markup)
            return
        except Exception as e:
            logger.warning(f"HTML send failed: {e}. Falling back to plaintext.")
            fallback_text = f"{text}\n\n{footer}" if footer else text
            await msg_handle.reply_text(fallback_text[:4000], reply_markup=reply_markup)
            return

    # 3. Jika terlalu panjang (> 4000), pecah menjadi chunks
    # Kirim disclaimer dulu
    if disclaimer:
        try:
            await msg_handle.reply_text(disclaimer, parse_mode="HTML")
        except Exception:
            await msg_handle.reply_text("⚠️ **Hasil Evaluasi:**")

    chunks = _split_message(text, 3500)
    if not chunks and text:
        chunks = [text] # Fallback jika splitter gagal
        
    for i, chunk in enumerate(chunks):
        chunk_html = safe_html(chunk)
        try:
            prefix = f"<b>[Bagian {i+1}/{len(chunks)}]</b>\n" if len(chunks) > 1 else ""
            await msg_handle.reply_text(prefix + chunk_html, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Chunk {i} HTML failed: {e}")
            await msg_handle.reply_text(chunk)
        
        await asyncio.sleep(0.8)

    # Kirim footer di akhir
    if footer:
        try:
            await msg_handle.reply_text(footer, parse_mode="HTML", reply_markup=reply_markup)
        except Exception:
            await msg_handle.reply_text("✅ Selesai.", reply_markup=reply_markup)

    # 4. FILE FALLBACK: Jika > 1 chunk, kirim file lengkap agar user punya backup
    if len(chunks) > 1:
        try:
            file_content = f"{disclaimer}\n\n{text}\n\n{footer}"
            bio = io.BytesIO(file_content.encode('utf-8'))
            bio.name = "hasil_evaluasi_lengkap.txt"
            await update.message.reply_document(
                document=bio,
                caption="📄 **File Backup**: Hasil evaluasi lengkap (Gunakan jika pesan di atas terpotong).",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send file fallback: {e}")


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk perintah (command) yang tidak dikenal."""
    await update.message.reply_text(
        "❌ **Perintah tidak dikenal.**\n"
        "Silakan ketik /start untuk memulai kembali atau /help untuk bantuan.",
        parse_mode="Markdown",
    )


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk pesan teks/media yang tidak dikenal di luar alur atau salah format."""
    await update.message.reply_text(
        "🧐 **Maaf, saya tidak mengerti pesan tersebut.**\n\n"
        "Silakan ikuti instruksi menu yang aktif atau ketik /start untuk kembali ke menu utama.",
        parse_mode="Markdown",
    )


# ══════════════════════════════════════════════════════════════════════════
#  MAIN — Application Setup
# ══════════════════════════════════════════════════════════════════════════

async def post_init(application: Application) -> None:
    """Inisialisasi database di dalam event loop bot."""
    await init_db()

def main():
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("Siapkan environment variable BOT_TOKEN untuk Telegram")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .connect_timeout(30)
        .read_timeout(30)
        .concurrent_updates(True)
        .build()
    )

    # ── Group 0: Middleware (Dedup + Access Control) ───────────────────────
    app.add_handler(TypeHandler(Update, check_access_middleware), group=0)

    # ── Group 1: Handlers (Conversation + Standalone) ─────────────────────
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command),
        ],
        states={
            SELECTING_LANG: [
                CallbackQueryHandler(lang_callback, pattern="^lang_"),
            ],
            SELECTING_PROJECT: [
                CallbackQueryHandler(project_callback, pattern="^proj_"),
                CallbackQueryHandler(back_lang_callback, pattern="^back_lang$"),
            ],
            SELECTING_TASK: [
                CallbackQueryHandler(task_callback, pattern="^task_"),
                CallbackQueryHandler(back_proj_callback, pattern="^back_proj$"),
            ],
            SELECTING_SUBTASK: [
                CallbackQueryHandler(subtask_callback, pattern="^sub_"),
                CallbackQueryHandler(back_task_callback, pattern="^back_task$"),
            ],
            SELECTING_VCG_SUBTASK: [
                CallbackQueryHandler(vcg_subtask_callback, pattern="^vcgsub_"),
                CallbackQueryHandler(back_task_callback, pattern="^back_task$"),
            ],
            CONFIRMING_TASK: [
                CallbackQueryHandler(confirm_task_callback, pattern="^confirm_"),
                CallbackQueryHandler(back_task_callback, pattern="^back_task$"),
            ],
            SELECTING_TIER: [
                CallbackQueryHandler(tier_callback, pattern="^tier_"),
                CallbackQueryHandler(back_task_callback, pattern="^back_task$"),
            ],
            READY: [
                CommandHandler("mulai", mulai_handler),
            ],
            COLLECTING_USER_ASK: [
                CommandHandler("next", next_to_resp_a),
                CommandHandler("done", force_done_command),
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_user_ask),
            ],
            COLLECTING_RESP_A: [
                CommandHandler("next", next_to_resp_b),
                CommandHandler("done", force_done_command),
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_resp_a),
            ],
            COLLECTING_RESP_B: [
                CommandHandler("next", next_to_resp_c),
                CommandHandler("done", force_done_command),
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_resp_b),
            ],
            COLLECTING_RESP_C: [
                CommandHandler("next", process_segmented_input),
                CommandHandler("skip", process_segmented_input),
                CommandHandler("done", force_done_command),
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_resp_c),
            ],
            # ── Single-Shot state: PSR & Writing QA ───────────────────────
            COLLECTING_SINGLE_SHOT: [
                CommandHandler("next", next_process_single_shot),
                CommandHandler("done", next_process_single_shot),
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_single_shot),
            ],
            # ── VCG Image Flow States ──────────────────────────────────
            COLLECTING_VCG_PROMPT: [
                CommandHandler("next", vcg_next_to_image_a),
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_vcg_prompt),
            ],
            COLLECTING_VCG_IMAGE_A: [
                CommandHandler("next", vcg_next_to_image_b),
                MessageHandler(filters.PHOTO, collect_vcg_image_a),
            ],
            COLLECTING_VCG_IMAGE_B: [
                CommandHandler("next", vcg_next_to_image_c),
                MessageHandler(filters.PHOTO, collect_vcg_image_b),
            ],
            COLLECTING_VCG_IMAGE_C: [
                CommandHandler("next", vcg_next_step_after_image_c),
                CommandHandler("skip", process_vcg_images),
                MessageHandler(filters.PHOTO, collect_vcg_image_c),
            ],
            COLLECTING_VCG_IMAGE_D: [
                CommandHandler("next", process_vcg_images),
                MessageHandler(filters.PHOTO, collect_vcg_image_d),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CommandHandler("start", start_command),
            CommandHandler("mulai", mulai_outside_ready),
        ],
        name="pr_evaluation_conversation",
        persistent=False,
    )

    # 1. Admin Commands
    app.add_handler(CommandHandler(["add_balance", "add"], add_balance_command), group=1)
    
    # 1.5 User Deposit Flow
    deposit_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("deposit", user_deposit_start)],
        states={
            DEPOSIT_ASK_NOMINAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_deposit_nominal)]
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        name="deposit_conversation",
    )
    app.add_handler(deposit_conv_handler, group=1)
    
    app.add_handler(CommandHandler("stats", stats_command), group=1)
    app.add_handler(CommandHandler("broadcast", broadcast_command), group=1)
    app.add_handler(CommandHandler("check_fail", check_fail_command), group=1)
    app.add_handler(CommandHandler("user", user_inspector_command), group=1)
    app.add_handler(CommandHandler("maintenance", toggle_maintenance_command), group=1)

    # 2. Standalone & User Commands
    app.add_handler(CommandHandler("status", status_command), group=1)
    app.add_handler(CommandHandler("help", help_command), group=1)
    app.add_handler(CommandHandler("history", history_command), group=1)

    # 3. Callback Queries (History & Feedback)
    app.add_handler(CallbackQueryHandler(feedback_callback, pattern="^feed_"), group=1)
    app.add_handler(CallbackQueryHandler(view_history_callback, pattern="^hist_view_"), group=1)

    # 4. State Machine
    app.add_handler(conv_handler, group=1)

    # 4. Unknown Message/Command Handler (Catch-all)
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command), group=1)
    app.add_handler(MessageHandler(filters.ALL, unknown_message), group=1)

    # ── Start: Webhook or Polling ─────────────────────────────────────────
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    PORT = int(os.environ.get("PORT", "8443"))

    if WEBHOOK_URL:
        logger.info(f"🤖 Bot starting via Webhook on port {PORT}...")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}",
        )
    else:
        logger.info("🤖 Bot is polling... (Credit-Based Billing active)")
        app.run_polling()


if __name__ == "__main__":
    main()

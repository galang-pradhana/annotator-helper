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
from core.config import *
from handlers.menus import *
from handlers.tasks_text import *
from handlers.tasks_vcg import *
from handlers.history import *
from handlers.standalone import status_command, help_command, unknown_command, unknown_command_handler, unknown_message
from utils.helpers import _parse_evaluation_input, send_large_message, _split_message
from services.evaluation import _run_evaluation_background, _run_vcg_evaluation_background, _calculate_dynamic_price, _extract_database_content, _format_user_input
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
    PicklePersistence,
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
from kie_api import call_ai_engine, call_ai_engine_multimodal, check_engine_status, test_ai_engine
from dotenv import set_key as dotenv_set_key

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
    maintenance_mode = context.bot_data.get("MAINTENANCE_MODE", False)
    if maintenance_mode and not is_admin:
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

    # BYPASS: Biarkan command utama lolos dari rate limit
    if text.startswith(("/start", "/cancel", "/deposit", "/add_balance", "/add", "/stats", "/help", "/status", "/history", "/user", "/broadcast", "/check_fail", "/maintenance", "/mulai", "/next", "/done", "/skip")):
        return


async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is admin."""
    return update.effective_user.id == ADMIN_ID


# ══════════════════════════════════════════════════════════════════════════
#  CONVERSATION HANDLERS — State Machine
# ══════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════
#  EVALUATION PROCESSING — Background Task with Refund Logic
# ══════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════
#  INPUT COLLECTORS — Multi-step data gathering
# ══════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════
#  SINGLE-SHOT COLLECTOR — PSR & Writing QA (kirim bertahap, /next evaluasi)
# ══════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════
#  VCG IMAGE COLLECTORS — Flow khusus untuk task Visual Content Generation
# ══════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════
#  ADMIN COMMANDS — /deposit, /stats, /broadcast, /check_fail, /user, /maintenance
# ══════════════════════════════════════════════════════════════════════════

from handlers.admin import (
    broadcast_command,
    check_fail_command,
    user_inspector_command,
    toggle_maintenance_command,
    switch_engine_command,
    check_engine_command,
    test_engine_command,
    add_balance_command,
    user_deposit_start,
    user_deposit_nominal,
    stats_command
)


# ══════════════════════════════════════════════════════════════════════════
#  STANDALONE HANDLERS (Group 2) — /status, /help
# ══════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS — Parsing & Splitting
# ══════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════
#  MAIN — Application Setup
# ══════════════════════════════════════════════════════════════════════════

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and handle specific telegram.error exceptions."""
    from telegram.error import BadRequest
    
    if isinstance(context.error, BadRequest):
        if "Message is not modified" in str(context.error):
            logger.debug("Ignored BadRequest: Message is not modified")
            return
            
    logger.error("Exception while handling an update:", exc_info=context.error)

async def post_init(application: Application) -> None:
    """Inisialisasi database di dalam event loop bot."""
    await init_db()

def main():
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("Siapkan environment variable BOT_TOKEN untuk Telegram")

    persistence = PicklePersistence(filepath="annotator_bot_data")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .persistence(persistence)
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
                CommandHandler("skip", skip_resp_b),
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
                CommandHandler("skip", process_vcg_images),
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
    app.add_handler(CommandHandler("switch", switch_engine_command), group=1)
    app.add_handler(CommandHandler("check", check_engine_command), group=1)
    app.add_handler(CommandHandler("test", test_engine_command), group=1)

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

    # 5. Global Error Handler
    app.add_error_handler(global_error_handler)

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

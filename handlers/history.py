import os
import html
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from database import get_session
import user_service
from services.evaluation import _calculate_dynamic_price, _run_evaluation_background, _run_vcg_evaluation_background
from utils.helpers import send_large_message, _split_message
from core.config import *
logger = logging.getLogger(__name__)

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

    import io
    
    date_str = eval_obj.timestamp.strftime("%Y-%m-%d %H:%M")
    
    file_content = (
        f"WAKTU: {date_str}\n"
        f"TASK: {eval_obj.task_code}\n"
        f"=========================================\n\n"
        f"USER INPUT:\n"
        f"{eval_obj.user_input}\n\n"
        f"=========================================\n\n"
        f"JAWABAN AI:\n"
        f"{eval_obj.ai_output}"
    )
    
    file_bytes = io.BytesIO(file_content.encode('utf-8'))
    file_bytes.name = f"History_{eval_obj.task_code}_{eval_obj.id}.md"
    
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=file_bytes,
        caption=f"📜 **Riwayat Evaluasi**\n📅 {date_str}\n📋 `{eval_obj.task_code}`",
        parse_mode="Markdown"
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



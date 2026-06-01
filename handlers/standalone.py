import os
from telegram import Update
from telegram.ext import ContextTypes
from database import get_session
import user_service
from core.config import ADMIN_ID, TIER_DISPLAY_LABELS, TIER_DISPLAY_RANGES

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

    status_text = (
        "📊 **Status Akun Anda**\n\n"
        f"👤 User ID: `{tg_id}`\n"
        f"🏷️ Username: `{user.username}`\n"
        f"💰 Saldo: **{user.balance:,} Poin**\n"
        f"🌍 Bahasa: `{user.selected_lang}`\n"
        f"📂 Proyek: `{user.selected_project}`\n"
        f"🛠️ Task: `{user.selected_task}`"
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
            "▫️ **/maintenance** `<on/off>` — Toggle mode perbaikan.\n"
            "▫️ **/switch** `<kie|openrouter>` — Ganti engine AI aktif.\n"
            "▫️ **/check engine** — Cek kesehatan server AI.\n"
            "▫️ **/test** `<basic|pro>` — Tes pengerjaan nyata ke AI aktif."
        )

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command yang tidak dikenali."""
    await update.message.reply_text(
        "❓ Maaf, perintah tersebut tidak dikenali.\n"
        "Gunakan /help untuk melihat daftar perintah yang tersedia."
    )


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



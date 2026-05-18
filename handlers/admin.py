import os
import random
import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from dotenv import set_key as dotenv_set_key

from core.config import ADMIN_ID, DEPOSIT_ASK_NOMINAL, MAINTENANCE_MODE
from database import get_session
import user_service
from kie_api import check_engine_status, test_ai_engine

logger = logging.getLogger(__name__)

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
    
    # Needs to modify a global flag. For clean architecture, 
    # MAINTENANCE_MODE shouldn't be just a local variable.
    # In this refactor we can use context.bot_data to share this state.
    current_status = context.bot_data.get("MAINTENANCE_MODE", False)
    args = context.args
    
    if not args:
        status_sekarang = "AKTIF 🚧" if current_status else "NON-AKTIF ✅"
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
        context.bot_data["MAINTENANCE_MODE"] = True
        await update.message.reply_text("🚧 **Maintenance Mode diaktifkan.** User biasa tidak dapat mengakses bot.", parse_mode="Markdown")
    elif command == "off":
        context.bot_data["MAINTENANCE_MODE"] = False
        await update.message.reply_text("✅ **Maintenance Mode dinonaktifkan.** Bot kini dapat diakses kembali oleh seluruh user.", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Argumen tidak dikenal. Gunakan `on` atau `off`.")


async def switch_engine_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /switch <kie|openrouter> — Ganti engine AI yang aktif secara global."""
    if update.effective_user.id != ADMIN_ID:
        return

    args = context.args
    if not args:
        current = os.environ.get("ACTIVE_ENGINE", "openrouter").upper()
        await update.message.reply_text(
            f"🔀 **Engine Switcher**\n\n"
            f"📍 Engine aktif saat ini: `{current}`\n\n"
            f"Gunakan:\n"
            f"`/switch kie` — Pindah ke Kie.ai\n"
            f"`/switch openrouter` — Pindah ke OpenRouter",
            parse_mode="Markdown"
        )
        return

    target = args[0].lower()
    if target not in ("kie", "openrouter"):
        await update.message.reply_text("❌ Pilihan tidak valid. Gunakan `kie` atau `openrouter`.")
        return

    os.environ["ACTIVE_ENGINE"] = target
    try:
        env_path = os.path.join(os.getcwd(), ".env")
        dotenv_set_key(env_path, "ACTIVE_ENGINE", target)
    except Exception as e:
        logger.warning(f"Gagal menyimpan ACTIVE_ENGINE ke .env: {e}")

    emoji = "🤖" if target == "kie" else "🔵"
    name = "Kie.ai" if target == "kie" else "OpenRouter"
    await update.message.reply_text(
        f"{emoji} **Engine berhasil diganti!**\n\n"
        f"📍 Engine aktif sekarang: `{name.upper()}`\n"
        f"Semua request AI dari seluruh user akan menggunakan **{name}** mulai sekarang.",
        parse_mode="Markdown"
    )
    logger.info(f"🔀 ADMIN switched engine to: {target.upper()}")


async def check_engine_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /check engine — Cek status kesehatan semua engine AI."""
    if update.effective_user.id != ADMIN_ID:
        return

    args = context.args
    if args and args[0].lower() == "engine" or not args:
        status_msg = await update.message.reply_text("⏳ Memeriksa status semua engine...")
        report = await check_engine_status()
        await status_msg.edit_text(report, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "📖 Gunakan: `/check engine`",
            parse_mode="Markdown"
        )


async def test_engine_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /test <basic|pro> — Melakukan tes pengerjaan nyata ke engine aktif."""
    if update.effective_user.id != ADMIN_ID:
        return

    args = context.args
    tier = "BASIC"
    if args:
        tier = args[0].upper()
        if tier not in ("BASIC", "PRO"):
            await update.message.reply_text("❌ Tier tidak valid. Gunakan `basic` atau `pro`.")
            return

    status_msg = await update.message.reply_text(f"🧪 Sedang mengetes engine aktif dengan tier `{tier}`...")
    report = await test_ai_engine(tier)
    await status_msg.edit_text(report, parse_mode="Markdown")


async def add_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /add_balance <user_id> <amount> — Top-up saldo user."""
    tg_id = update.effective_user.id
    logger.info(f"Add balance command received from {tg_id}. ADMIN_ID defined as: {ADMIN_ID}")
    
    if tg_id != ADMIN_ID:
        await update.message.reply_text("❌ Anda tidak memiliki akses admin.")
        return

    args = list(context.args) if context.args else []
    
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
        "🔢 No. Rekening: 6720373350\n"
        "👤 A/N: Yanuhar Prabowo\n\n"
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

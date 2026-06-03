import os
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import get_session
import user_service
from rag.retriever import retrieve_guideline_context, retrieve_guideline_context_with_meta
from kie_api import call_ai_engine_with_cost, AGENT_MARKUP
from utils.helpers import send_large_message
from core.config import AGENT_CHAT
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

def _get_agent_model() -> str:
    """Mengembalikan model yang sesuai dengan engine aktif untuk sesi Tanya Guideline."""
    engine = os.environ.get("ACTIVE_ENGINE", "openrouter").lower()
    if engine == "openrouter":
        return "deepseek-v3.2"
    else:
        return "gemini-3.5-flash"

async def agent_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mencari informasi di internet via DuckDuckGo dan mensintesiskannya menggunakan LLM."""
    import html
    import asyncio
    
    agent_model = _get_agent_model()
    
    query_text = update.message.text.replace('/cari', '').strip()
    if not query_text:
        await update.message.reply_text("❌ Format salah! Gunakan: `/cari [kata kunci/pertanyaan]`", parse_mode="Markdown")
        return AGENT_CHAT
        
    tg_id = update.effective_user.id
    task_code = context.user_data.get("SELECTED_TASK", "PR")
    sub_task = context.user_data.get("SELECTED_SUBTASK")
    target_task = sub_task if sub_task else task_code
    
    # Pre-check balance minimum untuk Pencarian & Sintesis (2 poin)
    async with get_session() as session:
        has_balance = await user_service.check_balance(session, tg_id, 2)
    if not has_balance:
        await update.message.reply_text(
            "❌ Saldo tidak mencukupi (Minimum 2 Poin) untuk melakukan pencarian & sintesis.\n"
            "Hubungi Admin untuk top-up."
        )
        return AGENT_CHAT
        
    status_msg = await update.message.reply_text("🔍 Merumuskan kata kunci pencarian...")
    
    try:
        # 1. Optimasi query pencarian menggunakan LLM
        search_query_prompt = f"""Kamu adalah asisten optimasi kata kunci mesin pencari.
Tugas kamu adalah mengekstrak 2 sampai 4 kata kunci pencarian bahasa Inggris atau Indonesia yang paling relevan, spesifik, dan efektif untuk mencari informasi di DuckDuckGo berdasarkan pertanyaan user.
Hanya kembalikan kata kunci pencarian saja, tanpa tanda kutip, tanpa kalimat pengantar, tanpa penjelasan tambahan.

Pertanyaan User: {query_text}
Kata Kunci Pencarian:"""
        optimized_query_response, _ = await call_ai_engine_with_cost(
            system_prompt="Kamu adalah pencari kata kunci pencarian yang akurat.",
            user_input=search_query_prompt,
            markup=AGENT_MARKUP,
            model_override=agent_model
        )
        
        optimized_query = optimized_query_response.strip().replace('"', '').replace("'", "")
        if not optimized_query:
            optimized_query = query_text
            
        logger.info(f"Query asli: '{query_text}' | Query dioptimalkan: '{optimized_query}'")
        
        await status_msg.edit_text(f"🌐 Mencari di web untuk: <i>'{html.escape(optimized_query)}'</i>...", parse_mode="HTML")
        
        # 2. Ambil data dari DuckDuckGo
        with DDGS() as ddgs:
            search_results = list(ddgs.text(optimized_query, max_results=4))
            
        if not search_results:
            await status_msg.edit_text("❌ Tidak ditemukan hasil pencarian web yang relevan untuk saat ini.")
            return AGENT_CHAT
            
        # 3. Format hasil pencarian untuk konteks LLM
        web_context = ""
        sources_list = []
        for i, res in enumerate(search_results, 1):
            title = res.get('title', 'No Title')
            href = res.get('href', '#')
            body = res.get('body', 'No Description')
            
            web_context += f"Sumber {i}: {title}\nURL: {href}\nDeskripsi: {body}\n\n"
            sources_list.append(f'<a href="{html.escape(href)}">{html.escape(title)}</a>')
            
        await status_msg.edit_text("🤖 Menganalisis dan menyusun jawaban guideline...")
        
        # 4. Sintesis dengan LLM
        system_prompt = f"""Kamu adalah AI Assistant khusus untuk Annotator Pro yang bertugas mensintesis hasil pencarian web untuk menjawab pertanyaan user.
Jawablah pertanyaan user dengan gaya penjelasan "Guideline resmi" yang sangat profesional, terstruktur, mendalam, dan relevan dengan task '{target_task}'.

Berikut adalah hasil pencarian internet yang relevan (gunakan informasi di bawah ini sebagai basis jawaban Anda):
---
{web_context}
---

Instruksi Tambahan:
- Berikan kriteria khusus, ciri khas, dan cara mengevaluasi/menilai gambar atau objek yang ditanyakan agar sesuai dengan standar guideline yang profesional.
- Sajikan jawaban dalam Bahasa Indonesia yang formal dan mudah dipahami.
- Jangan menggunakan markdown mentah untuk tautan seperti [Title](URL). Cukup fokus pada penjelasan. Bagian referensi sumber akan ditambahkan di luar respons utama.
"""
        
        llm_response, price = await call_ai_engine_with_cost(
            system_prompt=system_prompt,
            user_input=query_text,
            markup=AGENT_MARKUP,
            model_override=agent_model
        )
        
        if llm_response.startswith(("❌", "⚠️")):
            await status_msg.edit_text(f"❌ Gagal mensintesis jawaban dari LLM.\n\n{llm_response}")
            return AGENT_CHAT
            
        # 5. Tambahkan bagian referensi secara rapi
        references_section = "\n\n🌐 **Referensi Sumber Pencarian:**\n" + "\n".join(f"- {src}" for src in sources_list)
        full_response = llm_response + references_section
        
        # 6. Deduct balance
        async with get_session() as session:
            await user_service.deduct_balance(session, tg_id, price, f"Agent Web Search: {target_task}", agent_model)
            user = await user_service.get_user_info(session, tg_id)
            current_balance = user.balance
            
        # Send result
        await status_msg.delete()
        disclaimer = f"🌐 **Hasil Sintesis Pencarian Web ({target_task})** | 💰 Biaya: {price} Poin | 💳 Sisa: {current_balance} Poin\n\n"
        await send_large_message(update, full_response, disclaimer=disclaimer, force_text=True)
        
    except Exception as e:
        logger.error(f"Search & Synthesis Error: {e}")
        await status_msg.edit_text("❌ Gagal melakukan pencarian dan sintesis saat ini.")
        
    return AGENT_CHAT

async def agent_selesai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mengakhiri sesi chat agent dan kembali ke awal."""
    context.user_data.pop("APP_MODE", None)
    context.user_data.pop("AGENT_TASK", None)
    
    await update.message.reply_text(
        "✅ Sesi Tanya Guideline telah diakhiri.\n"
        "Ketik /start untuk memulai kembali.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def agent_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menerima pertanyaan user, mencari konteks dari guideline, dan menjawab dengan LLM."""
    import html as html_module

    agent_model = _get_agent_model()

    query_text = update.message.text
    if query_text.startswith('/'):
        return AGENT_CHAT
        
    tg_id = update.effective_user.id
    task_code = context.user_data.get("SELECTED_TASK", "PR")
    sub_task = context.user_data.get("SELECTED_SUBTASK")
    
    target_task = sub_task if sub_task else task_code
    
    # Pre-check balance minimum untuk Agent (2 poin)
    async with get_session() as session:
        has_balance = await user_service.check_balance(session, tg_id, 2)
    if not has_balance:
        await update.message.reply_text(
            "❌ Saldo tidak mencukupi (Minimum 2 Poin) untuk bertanya.\n"
            "Hubungi Admin untuk top-up."
        )
        return AGENT_CHAT
        
    status_msg = await update.message.reply_text("🔍 Sedang mencari di dokumen guideline...")
    
    try:
        # ── Step 1: Retrieve context dengan metadata ─────────────────────────
        rag_result = await retrieve_guideline_context_with_meta(
            query_text,
            task_code=target_task,
            top_k=6,
        )
        context_text  = rag_result["text"]
        chunk_count   = rag_result["chunk_count"]
        top_sim       = rag_result["top_similarity"]
        rag_source    = rag_result["source"]   # "guideline" | "cross_task" | "empty"
        
        # ── Step 2: Build system prompt berdasarkan ketersediaan context ─────
        is_visual_task = target_task.upper().startswith("VCG")
        visual_note = (
            "Task ini berbasis GAMBAR/VISUAL (VCG). "
            "Kamu boleh membahas aspek visual, gambar, image quality, dan sejenisnya."
        ) if is_visual_task else (
            "Task ini berbasis TEKS (non-visual). "
            "JANGAN membahas gambar, visual, image quality, atau aspek visual apapun. "
            "Fokus hanya pada aspek evaluasi teks, instruksi, konten, dan bahasa."
        )

        has_context = bool(context_text)

        if has_context:
            # ── MODE A: Jawab STRICT dari dokumen guideline ──────────────────
            system_prompt = f"""Kamu adalah AI Assistant khusus untuk task '{target_task}' di Annotator Pro.
{visual_note}

=== INSTRUKSI WAJIB — BACA DAN PATUHI SEPENUHNYA ===
1. Jawab HANYA berdasarkan CONTEXT GUIDELINE yang diberikan di bawah.
2. JANGAN menambahkan informasi dari luar context, sekecil apapun.
3. JANGAN menjawab pertanyaan yang tidak berkaitan dengan task '{target_task}'.
4. Jika context tidak membahas pertanyaan secara spesifik, nyatakan dengan jelas:
   "Berdasarkan dokumen guideline yang tersedia, saya tidak menemukan informasi spesifik 
   tentang ini. Gunakan /cari [keyword] untuk pencarian internet."
5. Struktur jawaban:
   - Gunakan bullet point atau numbered list untuk kejelasan
   - Sebutkan dari bagian mana informasi berasal (contoh: "Berdasarkan bagian Structural Integrity...")
   - Jawab dalam Bahasa Indonesia yang profesional
6. Jangan berikan disclaimer panjang — cukup jawab langsung dan faktual.

=== CONTEXT GUIDELINE (SUMBER KEBENARAN — JANGAN DIABAIKAN) ===
{context_text}
=== END OF CONTEXT ==="""
        else:
            # ── MODE B: Context kosong — jawab dengan disclaimer jelas ───────
            system_prompt = f"""Kamu adalah AI Assistant khusus untuk task '{target_task}' di Annotator Pro.
{visual_note}

=== INSTRUKSI PENTING ===
Dokumen guideline spesifik untuk pertanyaan ini TIDAK DITEMUKAN dalam database.
Kamu HARUS:
1. Tetap berikan jawaban berdasarkan pengetahuan umum tentang task annotasi/evaluasi AI
2. WAJIB menyebut di awal jawaban bahwa ini bukan dari dokumen guideline resmi
3. Sarankan user untuk menggunakan /cari [keyword] untuk informasi lebih akurat
4. Jangan berikan informasi yang bisa menyesatkan annotator

Jawab dalam Bahasa Indonesia yang profesional."""
        
        await status_msg.edit_text("🤖 Merumuskan jawaban...")
        
        # ── Step 3: Panggil LLM ──────────────────────────────────────────────
        llm_response, price = await call_ai_engine_with_cost(
            system_prompt=system_prompt,
            user_input=query_text,
            markup=AGENT_MARKUP,
            model_override=agent_model
        )
        
        if llm_response.startswith(("❌", "⚠️")):
            await status_msg.edit_text(f"❌ Gagal mendapatkan jawaban dari LLM.\n\n{llm_response}")
            return AGENT_CHAT
        
        # ── Step 4: Deduct balance ───────────────────────────────────────────
        async with get_session() as session:
            await user_service.deduct_balance(session, tg_id, price, f"Agent Query: {target_task}", agent_model)
            user = await user_service.get_user_info(session, tg_id)
            current_balance = user.balance
            
        # ── Step 5: Bangun header & disclaimer berdasarkan hasil RAG ─────────
        await status_msg.delete()

        if has_context:
            sim_pct = int(top_sim * 100)
            if rag_source == "cross_task":
                source_label = (
                    f"📚 Sumber: {chunk_count} bagian guideline (lintas task, relevansi: {sim_pct}%)\n"
                    f"<i>⚠️ Guideline spesifik untuk {html_module.escape(target_task)} tidak ditemukan, menampilkan hasil terdekat.</i>"
                )
            else:
                source_label = (
                    f"📚 Sumber: {chunk_count} bagian guideline "
                    f"<b>{html_module.escape(target_task)}</b> (relevansi: {sim_pct}%)"
                )
            disclaimer = (
                f"📋 <b>Jawaban Guideline</b> | {html_module.escape(target_task)}\n"
                f"{source_label}\n"
                f"{'─' * 35}\n\n"
            )
            footer = (
                f"\n\n{'─' * 35}\n"
                f"💰 Biaya: <b>{price} Poin</b> | 💳 Sisa: <b>{current_balance} Poin</b>"
            )
        else:
            disclaimer = (
                f"⚠️ <b>Jawaban Guideline</b> | {html_module.escape(target_task)}\n"
                f"📋 Sumber: <i>Pengetahuan umum (guideline tidak ditemukan di database)</i>\n"
                f"{'─' * 35}\n\n"
            )
            footer = (
                f"\n\n{'─' * 35}\n"
                f"💡 Untuk info akurat: <code>/cari [keyword]</code>\n"
                f"💰 Biaya: <b>{price} Poin</b> | 💳 Sisa: <b>{current_balance} Poin</b>"
            )

        await send_large_message(
            update,
            llm_response,
            disclaimer=disclaimer,
            footer=footer,
            force_text=True,
        )
        
    except Exception as e:
        logger.error(f"Agent Chat Error: {e}")
        await status_msg.edit_text("❌ Terjadi kesalahan saat memproses pertanyaan Anda. Coba lagi nanti.")
        
    return AGENT_CHAT

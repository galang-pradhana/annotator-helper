import re
import io
import asyncio
import logging
from telegram import Update, InlineKeyboardMarkup

logger = logging.getLogger(__name__)
import telegram.error

async def _retry_telegram_call(func, *args, retries=3, delay=2.0, **kwargs):
    """Mencoba ulang panggilan Telegram API untuk mengatasi masalah koneksi/timeout (terutama setelah AI processing lama)."""
    for attempt in range(1, retries + 1):
        try:
            return await func(*args, **kwargs)
        except (telegram.error.TimedOut, telegram.error.NetworkError) as e:
            logger.warning(f"Telegram API Timeout/NetworkError (attempt {attempt}/{retries}): {e}")
            if attempt == retries:
                raise
            await asyncio.sleep(delay)


def _safe_html(t: str) -> str:
    """Konversi teks ke HTML-safe dengan Markdown dasar (bold, code, bullet)."""
    if not t:
        return ""
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', t, flags=re.DOTALL)
    t = re.sub(r'`(.*?)`', r'<code>\1</code>', t)
    t = re.sub(r'(?m)^\* ', r'• ', t)
    return t

def _split_message(text: str, chunk_size: int = 3500) -> list:
    """Memecah teks panjang berdasarkan newline terdekat."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    while text:
        if len(text) <= chunk_size:
            chunks.append(text)
            break
            
        split_point = text.rfind("\n", 0, chunk_size)
        if split_point == -1:
            split_point = chunk_size
            
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
    force_text: bool = False,
) -> None:
    """
    Mengirim pesan panjang ke user dengan cara:
    1. Jika force_text=True, kirim full text langsung sebagai pesan telegram (dipecah per 3800 karakter jika perlu).
    2. Jika force_text=False:
       - Konversi ke HTML untuk kestabilan parsing.
       - Jika > 3800 karakter, JANGAN pecah-pecah pesan (menghindari FloodWait & pemotongan tag).
         Kirim langsung sebagai file Document (.txt/.md) lengkap.
    """
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:[a-zA-Z]*)\n?", "", text, count=1)
    if text.endswith("```"):
        text = re.sub(r"\n?```$", "", text, count=1)
    text = text.strip()

    msg_handle = update.effective_message if update.effective_message else update.message
    if not msg_handle:
        logger.error("Tidak dapat menemukan message handle untuk mengirim respons.")
        return

    if force_text:
        # Gabungkan disclaimer + text + footer ke dalam satu pesan utuh jika memungkinkan, atau pecah
        full_text = ""
        if disclaimer:
            full_text += disclaimer + "\n"
        full_text += text
        if footer:
            full_text += "\n" + footer
            
        # Gunakan _safe_html untuk kestabilan parsing tanpa crash
        full_html = _safe_html(full_text)
        
        chunks = _split_message(full_html, chunk_size=3800)
        for i, chunk in enumerate(chunks):
            if i > 0:
                await asyncio.sleep(1.0)
            is_last = (i == len(chunks) - 1)
            await _retry_telegram_call(
                msg_handle.reply_text,
                chunk,
                parse_mode="HTML",
                read_timeout=30,
                write_timeout=30,
                reply_markup=reply_markup if is_last else None,
            )
        return

    content_html = _safe_html(text)
    
    full_html = ""
    if disclaimer:
        full_html += disclaimer + "\n"
    full_html += content_html
    if footer:
        full_html += "\n" + footer

    # Kirim selalu sebagai file Markdown / text untuk keseragaman output
    # Langkah 1: kirim disclaimer + footer dulu
    if disclaimer:
        try:
            intro = disclaimer
            if footer:
                intro += f"\n(Hasil terlalu panjang, dikirim sebagai file di bawah ini.)\n\n{footer}"
            await _retry_telegram_call(
                msg_handle.reply_text,
                intro, parse_mode="HTML", read_timeout=30, write_timeout=30
            )
        except Exception as e:
            logger.warning(f"Disclaimer send failed: {e}")
            try:
                await _retry_telegram_call(
                    msg_handle.reply_text,
                    "⚠️ Hasil evaluasi (terlalu panjang, lihat file di bawah).", read_timeout=30, write_timeout=30
                )
            except Exception:
                pass

    # Langkah 2: kirim sebagai file dokumen
    doc_sent = False
    try:
        # Tambahkan jeda untuk mencegah FloodWait dari Telegram API
        if disclaimer:
            await asyncio.sleep(1.5)
            
        file_bytes = text.encode('utf-8')
        await _retry_telegram_call(
            msg_handle.reply_document,
            document=file_bytes,
            filename="hasil_evaluasi.md",
            caption="📄 <b>Hasil Evaluasi AI</b> (Buka untuk membaca keseluruhan teks tanpa terpotong).",
            parse_mode="HTML",
            reply_markup=reply_markup,
            read_timeout=60,
            write_timeout=120,
        )
        doc_sent = True
    except Exception as e:
        logger.error(f"reply_document failed: {type(e).__name__}: {e}")

    # Langkah 3: fallback — pecah dan kirim sebagai teks biasa
    if not doc_sent:
        logger.warning("Dokumen gagal dikirim. Mencoba kirim sebagai teks terpecah...")
        try:
            chunks = _split_message(text, chunk_size=3500)
            for i, chunk in enumerate(chunks):
                if i > 0:
                    await asyncio.sleep(1.5) # Jeda antar pesan agar tidak FloodWait
                    
                is_last = (i == len(chunks) - 1)
                await _retry_telegram_call(
                    msg_handle.reply_text,
                    chunk,
                    read_timeout=30,
                    write_timeout=30,
                    reply_markup=reply_markup if is_last else None,
                )
        except Exception as e:
            logger.error(f"Chunked text fallback juga gagal: {type(e).__name__}: {e}")
            try:
                await _retry_telegram_call(
                    msg_handle.reply_text,
                    "❌ Gagal mengirim hasil evaluasi ke Telegram.\n"
                    "Kemungkinan koneksi lambat atau ukuran respons terlalu besar.\n"
                    "Silakan coba lagi.",
                    read_timeout=30,
                    write_timeout=30,
                )
            except Exception:
                pass
def _parse_evaluation_input(text: str, input_list: list = None, task_type: str = "") -> tuple | None:
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

    # ── KHUSUS: TA_WRITING_TOOLS_CONTEXTUAL_SYNONYMS ───────────────────
    # Input: Original text, A1..A4, B1..B4
    if task_type == "TA_WRITING_TOOLS_CONTEXTUAL_SYNONYMS" and input_list and "__JUMP__" in input_list:
        jump_idx = input_list.index("__JUMP__")
        a_responses = input_list[1:jump_idx]
        b_responses = input_list[jump_idx+1:]
        
        orig = input_list[0] if len(input_list) > 0 else ""
        a1 = a_responses[0] if len(a_responses) > 0 else ""
        a2 = a_responses[1] if len(a_responses) > 1 else ""
        a3 = a_responses[2] if len(a_responses) > 2 else ""
        a4 = a_responses[3] if len(a_responses) > 3 else ""
        
        b1 = b_responses[0] if len(b_responses) > 0 else ""
        b2 = b_responses[1] if len(b_responses) > 1 else ""
        b3 = b_responses[2] if len(b_responses) > 2 else ""
        b4 = b_responses[3] if len(b_responses) > 3 else ""
        
        if orig and (a1 or b1):
            return (orig, a1, a2, a3, a4, b1, b2, b3, b4)
    cs_patterns = {
        "orig": r"(?i)(?:Original\s*text\s*:?\s*)([\s\S]*?)(?=(?:Response\s*A1\s*:?)|$)",
        "a1":   r"(?i)(?:Response\s*A1\s*:?\s*)([\s\S]*?)(?=(?:Response\s*A2\s*:?)|(?:Response\s*A3\s*:?)|(?:Response\s*A4\s*:?)|(?:Response\s*B1\s*:?)|$)",
        "a2":   r"(?i)(?:Response\s*A2\s*:?\s*)([\s\S]*?)(?=(?:Response\s*A3\s*:?)|(?:Response\s*A4\s*:?)|(?:Response\s*B1\s*:?)|$)",
        "a3":   r"(?i)(?:Response\s*A3\s*:?\s*)([\s\S]*?)(?=(?:Response\s*A4\s*:?)|(?:Response\s*B1\s*:?)|$)",
        "a4":   r"(?i)(?:Response\s*A4\s*:?\s*)([\s\S]*?)(?=(?:Response\s*B1\s*:?)|$)",
        "b1":   r"(?i)(?:Response\s*B1\s*:?\s*)([\s\S]*?)(?=(?:Response\s*B2\s*:?)|(?:Response\s*B3\s*:?)|(?:Response\s*B4\s*:?)|$)",
        "b2":   r"(?i)(?:Response\s*B2\s*:?\s*)([\s\S]*?)(?=(?:Response\s*B3\s*:?)|(?:Response\s*B4\s*:?)|$)",
        "b3":   r"(?i)(?:Response\s*B3\s*:?\s*)([\s\S]*?)(?=(?:Response\s*B4\s*:?)|$)",
        "b4":   r"(?i)(?:Response\s*B4\s*:?\s*)([\s\S]*?)$",
    }

    cs_orig = _regex_extract(text, cs_patterns["orig"])
    cs_a1 = _regex_extract(text, cs_patterns["a1"])
    cs_a2 = _regex_extract(text, cs_patterns["a2"])
    cs_a3 = _regex_extract(text, cs_patterns["a3"])
    cs_a4 = _regex_extract(text, cs_patterns["a4"])
    cs_b1 = _regex_extract(text, cs_patterns["b1"])
    cs_b2 = _regex_extract(text, cs_patterns["b2"])
    cs_b3 = _regex_extract(text, cs_patterns["b3"])
    cs_b4 = _regex_extract(text, cs_patterns["b4"])

    if cs_orig and (cs_a1 or cs_b1):
        return (cs_orig, cs_a1, cs_a2, cs_a3, cs_a4, cs_b1, cs_b2, cs_b3, cs_b4)

    # ── DEFAULT: PR, TC, CYU, AFM ──────────────────────────────────────
    # Coba format 1: split by separator ---
    if "---" in text:
        sections = [s.strip() for s in text.split("---")]
        if len(sections) >= 2: # Minimal 2 section (Input + Resp)
            # Detect label di section pertama
            first_sec = sections[0]
            if re.match(r"^\s*(?:Instruction|User\s*Input|Original\s*Input\s*Text|Original\s*Text|User\s*Ask|User)\s*:", first_sec, re.IGNORECASE):
                user_ask = re.sub(r"^\s*(?:Instruction|User\s*Input|Original\s*Input\s*Text|Original\s*Text|User\s*Ask|User)\s*:\s*", "", first_sec, flags=re.IGNORECASE).strip()
            else:
                user_ask = first_sec # Fallback jika tidak ada label tapi ada separator

            responses = []
            for i in range(1, len(sections)):
                label = chr(65 + i - 1)
                if i == 1:
                    resp = _strip_label(sections[1], "Response A")
                    if not resp:
                        resp = _strip_label(sections[1], "Response")
                else:
                    resp = _strip_label(sections[i], f"Response {label}")
                responses.append(resp)
            
            if user_ask and responses:
                return (user_ask, *responses)

    # Coba format 2: regex-based extraction
    user_ask_pattern = r"(?i)(?:(?:Instruction|User\s*Ask|Original\s*(?:Input\s*)?Text|User\s*Input|User|Conversation|\[CONVERSATION\])\s*:?\s*)([\s\S]*?)(?=Response\s*(?:A|:)|\[RESPONSE\s*A\]|$)"
    user_ask = _regex_extract(text, user_ask_pattern)

    responses = []
    for i in range(7):  # Up to G (A,B,C,D,E,F,G)
        letter = chr(65 + i)
        next_letter = chr(65 + i + 1)
        
        if i == 0:
            pattern = rf"(?i)(?:(?:Response\s*(?:A\s*)?|\[RESPONSE\s*A\])\s*:?\s*)([\s\S]*?)(?=Response\s*{next_letter}\s*:|\[RESPONSE\s*{next_letter}\]|$)"
        else:
            pattern = rf"(?i)(?:(?:Response\s*{letter}\s*|\[RESPONSE\s*{letter}\])\s*:?\s*)([\s\S]*?)(?=Response\s*{next_letter}\s*:|\[RESPONSE\s*{next_letter}\]|$)"
            
        resp = _regex_extract(text, pattern)
        if not resp:
            break
        responses.append(resp)

    if user_ask and responses:
        return (user_ask, *responses)

    return None


def _strip_label(text: str, label: str) -> str:
    """Hapus label prefix seperti 'User Ask:', 'Response A:', dll."""
    pattern = re.compile(rf"^\s*{re.escape(label)}\s*:\s*", re.IGNORECASE)
    return pattern.sub("", text).strip()


def _regex_extract(text: str, pattern: str) -> str:
    """Extract content dari regex pattern."""
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def is_balance_sufficient(current_balance: int, price: int) -> bool:
    """Cek apakah saldo mencukupi untuk harga tertentu."""
    return current_balance >= price



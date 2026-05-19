import re
import io
import asyncio
import logging
from telegram import Update, InlineKeyboardMarkup

logger = logging.getLogger(__name__)


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
) -> None:
    """
    Mengirim pesan panjang ke user dengan cara:
    1. Konversi ke HTML untuk kestabilan parsing.
    2. Jika > 3800 karakter, JANGAN pecah-pecah pesan (menghindari FloodWait & pemotongan tag).
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

    content_html = _safe_html(text)
    
    full_html = ""
    if disclaimer:
        full_html += disclaimer + "\n"
    full_html += content_html
    if footer:
        full_html += "\n" + footer

    # Opsi A: Jika pendek, kirim sbg HTML. Jika panjang, kirim dokumen instan.
    if len(full_html) <= 3800:
        try:
            await msg_handle.reply_text(full_html, parse_mode="HTML", reply_markup=reply_markup, read_timeout=30, write_timeout=30)
            return
        except Exception as e:
            logger.warning(f"HTML send failed: {e}. Falling back to document.")

    # Kirim sebagai file Markdown / text
    try:
        if disclaimer:
            try:
                intro = disclaimer
                if footer:
                    intro += f"\n(Hasil terlalu panjang, dikirim sebagai file di bawah ini.)\n\n{footer}"
                await msg_handle.reply_text(intro, parse_mode="HTML", read_timeout=30, write_timeout=30)
            except Exception:
                await msg_handle.reply_text("⚠️ **Hasil Evaluasi:**\nTerlalu panjang, lihat file di bawah.", read_timeout=30, write_timeout=30)
        
        file_content = f"{text}"
        bio = io.BytesIO(file_content.encode('utf-8'))
        bio.name = "hasil_evaluasi.md"
        await update.message.reply_document(
            document=bio,
            caption="📄 **Hasil Evaluasi AI** (Buka untuk membaca keseluruhan teks tanpa terpotong).",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Failed to send file fallback: {e}")
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
            if re.match(r"^\s*(?:Instruction|User\s*Input|Original\s*Input\s*Text|Original\s*Text|User\s*Ask|User)\s*:", first_sec, re.IGNORECASE):
                user_ask = re.sub(r"^\s*(?:Instruction|User\s*Input|Original\s*Input\s*Text|Original\s*Text|User\s*Ask|User)\s*:\s*", "", first_sec, flags=re.IGNORECASE).strip()
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
        "user_ask": r"(?i)(?:(?:Instruction|User\s*Ask|Original\s*(?:Input\s*)?Text|User\s*Input|User)\s*:\s*)([\s\S]*?)(?=Response\s*(?:A|:)|$)",
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


def is_balance_sufficient(current_balance: int, price: int) -> bool:
    """Cek apakah saldo mencukupi untuk harga tertentu."""
    return current_balance >= price



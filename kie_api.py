"""
kie_api.py
----------
API client untuk Kie.ai LLM (Gemini 3.1 Pro / Claude Sonnet 4.6).
Dipanggil oleh bot setelah prompt assembly selesai.

Endpoint:
  - Gemini : POST https://api.kie.ai/{model}/v1/chat/completions  (OpenAI format)
  - Claude : POST https://api.kie.ai/claude/v1/messages            (Anthropic format)

Error Classification:
  - code 500 + "maintained" → MAINTENANCE (bisa retry)
  - code 500 + lain-lain   → SERVER ERROR (retry 1x saja lalu bail)
  - code 400/401/403       → CLIENT ERROR (jangan retry, langsung bail)
"""

import os
import asyncio
import logging
import httpx

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Retry Config ──────────────────────────────────────────────────────────────
MAX_RETRIES = 2       # Jumlah percobaan ulang maksimal setelah gagal pertama
RETRY_DELAY = 3.0     # Detik jeda antar retry (exponential backoff)


def _is_maintenance_error(msg: str) -> bool:
    """Deteksi apakah error 500 adalah karena server maintenance."""
    maintenance_keywords = [
        "maintained",
        "maintenance",
        "under maintenance",
    ]
    msg_lower = (msg or "").lower()
    return any(kw in msg_lower for kw in maintenance_keywords)


async def call_kie_ai_api(
    system_prompt: str,
    user_input: str,
    model_override: str = None,
) -> str:
    """
    Mengirim system prompt + user input ke Kie.ai API dan mengembalikan respons LLM.

    Args:
        system_prompt : Master system prompt yang sudah dirakit oleh prompt_assembler.
        user_input    : Input user (User Ask + Response A/B/C).
        model_override: Jika diisi, gunakan model ini (BASIC → gemini, PREMIUM → claude).

    Returns:
        String respons dari LLM, atau pesan error dengan prefix ❌/⚠️.
    """

    api_url   = os.environ.get("KIE_API_URL", "")
    api_key   = os.environ.get("KIE_API_KEY") or os.environ.get("KIE_AI_API_KEY", "")
    model_name = model_override or os.environ.get("KIE_MODEL", "gemini-3.1-pro")
    timeout   = int(os.environ.get("KIE_TIMEOUT", "120"))

    # ── Fallback DUMMY jika API belum diset ──────────────────────────────────
    if not api_url or not api_key:
        logger.warning(
            f"KIE_API_URL atau KIE_API_KEY belum diset. Mode DUMMY aktif."
        )
        return (
            "⚠️ **Mode Demo** — API belum dikonfigurasi.\n\n"
            "System prompt berhasil dirakit dan siap dikirim.\n"
            f"Panjang system prompt: {len(system_prompt)} karakter.\n\n"
            "Untuk mengaktifkan, set `KIE_API_URL` dan `KIE_API_KEY` di `.env`.\n\n"
            "---\n"
            f"**Input Anda (echo):**\n```\n{user_input}\n```"
        )

    is_claude = model_name.lower().startswith("claude")
    base_url  = api_url.rstrip("/")

    if is_claude:
        # ── Anthropic format — gunakan field `system` terpisah ───────────────
        # Dokumentasi kie.ai: POST https://api.kie.ai/claude/v1/messages
        # PENTING: system_prompt masuk ke `system`, BUKAN ke messages.content
        target_endpoint = f"{base_url}/claude/v1/messages"
        payload = {
            "model": model_name,
            "system": system_prompt,          # ← Field terpisah, lebih efisien
            "messages": [
                {"role": "user", "content": user_input},
            ],
            "max_tokens": 8192,
            "thinkingFlag": True,             # ← Enable thinking mode sesuai dok
            "stream": False,
        }
    else:
        # ── OpenAI-compatible format (Gemini) ────────────────────────────────
        # Dokumentasi kie.ai: POST https://api.kie.ai/{model}/v1/chat/completions
        target_endpoint = f"{base_url}/{model_name}/v1/chat/completions"
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_input},
            ],
            "temperature": 0.3,
            "max_tokens": 8192,
        }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    logger.info(
        f"🚀 KIE.AI REQUEST | MODEL: {model_name} | "
        f"ENDPOINT: {target_endpoint} | "
        f"PROMPT: {len(system_prompt)} chars | INPUT: {len(user_input)} chars"
    )

    # ── Retry loop ────────────────────────────────────────────────────────────
    last_error_msg = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(f"Attempt {attempt}/{MAX_RETRIES} → {target_endpoint}")
                response = await client.post(target_endpoint, json=payload, headers=headers)

                # ── HTTP-level error ─────────────────────────────────────────
                if response.status_code != 200:
                    raw = response.text[:600]
                    logger.error(
                        f"[{attempt}] HTTP {response.status_code} from Kie.ai: {raw}"
                    )
                    last_error_msg = f"HTTP {response.status_code}: {raw}"

                    # Client error (4xx) → jangan retry
                    if 400 <= response.status_code < 500:
                        return (
                            f"❌ **Client Error {response.status_code}**\n"
                            f"```\n{raw}\n```\n"
                            "(Saldo tidak dipotong — periksa konfigurasi request)"
                        )

                    # Server error (5xx) → cek apakah maintenance
                    if _is_maintenance_error(raw):
                        if attempt < MAX_RETRIES:
                            wait = RETRY_DELAY * attempt
                            logger.warning(f"Server maintenance detected. Retry in {wait}s...")
                            await asyncio.sleep(wait)
                            continue
                        return (
                            "❌ **Server Maintenance**\n"
                            "Kie.ai sedang dalam pemeliharaan. Coba lagi beberapa menit.\n"
                            "(Saldo tidak dipotong)"
                        )
                    else:
                        if attempt < MAX_RETRIES:
                            wait = RETRY_DELAY * attempt
                            logger.warning(f"Server error {response.status_code}. Retry in {wait}s...")
                            await asyncio.sleep(wait)
                            continue
                        return (
                            f"❌ **Server Error {response.status_code}**\n"
                            f"```\n{raw}\n```\n"
                            "(Saldo tidak dipotong — API sedang bermasalah)"
                        )

                # ── Parse JSON response ──────────────────────────────────────
                data = response.json()

                # Wrapped error (HTTP 200 tapi body mengandung code error)
                if isinstance(data, dict):
                    api_code = data.get("code")
                    if api_code and str(api_code) != "200":
                        api_msg = data.get("msg") or data.get("message") or "Unknown API error"
                        logger.error(f"[{attempt}] Kie.ai wrapped error {api_code}: {api_msg}")
                        last_error_msg = f"code {api_code}: {api_msg}"

                        if _is_maintenance_error(api_msg):
                            if attempt < MAX_RETRIES:
                                wait = RETRY_DELAY * attempt
                                logger.warning(f"Maintenance via wrapped error. Retry in {wait}s...")
                                await asyncio.sleep(wait)
                                continue
                            return (
                                "❌ **Server Maintenance**\n"
                                "Kie.ai sedang dalam pemeliharaan. Coba lagi beberapa menit.\n"
                                "(Saldo tidak dipotong)"
                            )
                        else:
                            # Server exception — retry 1x lalu bail
                            if attempt < MAX_RETRIES:
                                wait = RETRY_DELAY * attempt
                                logger.warning(f"Server exception. Retry in {wait}s...")
                                await asyncio.sleep(wait)
                                continue
                            return (
                                f"❌ **API Error {api_code}**\n"
                                f"> {api_msg}\n\n"
                                "(Saldo tidak dipotong — silakan coba lagi nanti)"
                            )

                # ── Extract LLM reply ────────────────────────────────────────
                llm_reply = ""

                if is_claude:
                    # Anthropic format: data["content"][0]["text"]
                    content = data.get("content", [])
                    if isinstance(content, list) and content:
                        for item in content:
                            # Skip thinking blocks, ambil text blocks saja
                            if isinstance(item, dict) and item.get("type") == "text":
                                llm_reply = item.get("text", "")
                                break
                        if not llm_reply:
                            # Fallback: ambil apapun dari item pertama
                            item = content[0]
                            if isinstance(item, dict):
                                llm_reply = item.get("text", str(item))
                            else:
                                llm_reply = str(item)
                    elif isinstance(content, str):
                        llm_reply = content
                else:
                    # OpenAI format: data["choices"][0]["message"]["content"]
                    choices = data.get("choices", [])
                    if choices:
                        llm_reply = choices[0].get("message", {}).get("content", "")

                if llm_reply:
                    credits = data.get("credits_consumed", "?")
                    logger.info(
                        f"✅ [{model_name}] Response OK | "
                        f"{len(llm_reply)} chars | credits: {credits}"
                    )
                    return llm_reply

                # Format tidak dikenali
                logger.warning(f"Unexpected Kie.ai response format: {list(data.keys())}")
                return (
                    f"⚠️ Format respons API tidak dikenali:\n"
                    f"```json\n{str(data)[:500]}\n```"
                )

        except httpx.TimeoutException:
            logger.error(f"[{attempt}] Kie.ai API timeout after {timeout}s")
            last_error_msg = "timeout"
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY * attempt)
                continue
            return (
                "❌ **Timeout** — API Kie.ai tidak merespons.\n"
                f"Batas waktu: {timeout} detik. Coba lagi nanti.\n"
                "(Saldo tidak dipotong)"
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"[{attempt}] HTTP Status Error: {e.response.status_code}")
            return (
                f"❌ **HTTP Error {e.response.status_code}**\n"
                f"```\n{e.response.text[:500]}\n```"
            )

        except Exception as e:
            logger.error(f"[{attempt}] Unexpected error: {type(e).__name__}: {e}")
            last_error_msg = f"{type(e).__name__}: {e}"
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY * attempt)
                continue
            return f"❌ **Error** — {type(e).__name__}: {e}"

    # Semua retry habis
    return (
        f"❌ **Gagal setelah {MAX_RETRIES} percobaan**\n"
        f"> {last_error_msg}\n\n"
        "(Saldo tidak dipotong — coba lagi nanti)"
    )


async def call_kie_ai_api_multimodal(
    system_prompt: str,
    user_text: str,
    images_b64: dict,
    model_override: str = None,
) -> str:
    """
    Mengirim system prompt + teks + gambar (base64) ke Kie.ai API.
    Dipakai khusus untuk task VCG (Visual Content Generation).

    Args:
        system_prompt : Master system prompt dari prompt_assembler.
        user_text     : Teks deskripsi input (User Prompt + keterangan gambar).
        images_b64    : Dict {"A": "<base64>", "B": "<base64>", "C": "<base64>"}.
        model_override: Override model (BASIC=gemini, PREMIUM=claude).

    Returns:
        String respons dari LLM.
    """
    api_url    = os.environ.get("KIE_API_URL", "")
    api_key    = os.environ.get("KIE_API_KEY") or os.environ.get("KIE_AI_API_KEY", "")
    model_name = model_override or os.environ.get("KIE_MODEL", "gemini-3.1-pro")
    timeout    = int(os.environ.get("KIE_TIMEOUT", "180"))

    # ── Fallback DUMMY ────────────────────────────────────────────────────────
    if not api_url or not api_key:
        logger.warning("KIE multimodal: API belum dikonfigurasi, mode DUMMY.")
        img_list = ", ".join(f"Gambar {k}" for k in images_b64.keys())
        return (
            "⚠️ **Mode Demo** — API belum dikonfigurasi.\n\n"
            f"VCG Multimodal siap: {len(images_b64)} gambar diterima ({img_list}).\n"
            f"System prompt: {len(system_prompt):,} karakter.\n\n"
            "Set `KIE_API_URL` dan `KIE_API_KEY` di `.env` untuk mengaktifkan.\n\n"
            "---\n"
            f"**User Prompt (echo):**\n```\n{user_text}\n```"
        )

    is_claude = model_name.lower().startswith("claude")
    base_url  = api_url.rstrip("/")

    # ── Susun content multimodal ──────────────────────────────────────────────
    if is_claude:
        content_parts = []
        for label, b64_data in images_b64.items():
            content_parts.append({"type": "text", "text": f"**Gambar {label}:**"})
            content_parts.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": b64_data,
                }
            })
        content_parts.append({"type": "text", "text": user_text})

        target_endpoint = f"{base_url}/claude/v1/messages"
        payload = {
            "model":       model_name,
            "system":      system_prompt,   # ← Field terpisah (konsisten dengan call_kie_ai_api)
            "messages":    [{"role": "user", "content": content_parts}],
            "max_tokens":  8192,
            "thinkingFlag": True,
            "stream":      False,
        }
    else:
        content_parts = []
        for label, b64_data in images_b64.items():
            content_parts.append({"type": "text", "text": f"**Gambar {label}:**"})
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}
            })
        content_parts.append({"type": "text", "text": user_text})

        target_endpoint = f"{base_url}/{model_name}/v1/chat/completions"
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": content_parts},
            ],
            "temperature": 0.3,
            "max_tokens":  8192,
        }

    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    logger.info(
        f"🖼️ VCG MULTIMODAL → KIE.AI | MODEL: {model_name} | "
        f"IMAGES: {list(images_b64.keys())} | PROMPT: {len(system_prompt)} chars"
    )

    # ── Retry loop ────────────────────────────────────────────────────────────
    last_error_msg = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(f"VCG Attempt {attempt}/{MAX_RETRIES}")
                response = await client.post(target_endpoint, json=payload, headers=headers)

                if response.status_code != 200:
                    raw = response.text[:600]
                    logger.error(f"[VCG-{attempt}] HTTP {response.status_code}: {raw}")
                    last_error_msg = f"HTTP {response.status_code}: {raw}"

                    if 400 <= response.status_code < 500:
                        return (
                            f"❌ **Client Error {response.status_code}**\n"
                            f"```\n{raw}\n```"
                        )
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(RETRY_DELAY * attempt)
                        continue
                    return (
                        f"❌ **Server Error {response.status_code}**\n"
                        f"```\n{raw}\n```\n"
                        "(Saldo tidak dipotong)"
                    )

                data = response.json()

                if isinstance(data, dict):
                    api_code = data.get("code")
                    if api_code and str(api_code) != "200":
                        api_msg = data.get("msg") or data.get("message") or "Unknown"
                        logger.error(f"[VCG-{attempt}] Wrapped error {api_code}: {api_msg}")
                        last_error_msg = f"code {api_code}: {api_msg}"
                        if attempt < MAX_RETRIES:
                            await asyncio.sleep(RETRY_DELAY * attempt)
                            continue
                        return (
                            f"❌ **API Error {api_code}**\n"
                            f"> {api_msg}\n\n"
                            "(Saldo tidak dipotong — silakan coba lagi)"
                        )

                llm_reply = ""
                if is_claude:
                    content = data.get("content", [])
                    if isinstance(content, list) and content:
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                llm_reply = item.get("text", "")
                                break
                        if not llm_reply:
                            item = content[0]
                            llm_reply = item.get("text", str(item)) if isinstance(item, dict) else str(item)
                    elif isinstance(content, str):
                        llm_reply = content
                else:
                    choices = data.get("choices", [])
                    if choices:
                        llm_reply = choices[0].get("message", {}).get("content", "")

                if llm_reply:
                    logger.info(f"✅ [VCG/{model_name}] Response OK | {len(llm_reply)} chars")
                    return llm_reply

                logger.warning(f"VCG unexpected response format: {list(data.keys())}")
                return (
                    f"⚠️ Format respons API tidak dikenali:\n"
                    f"```json\n{str(data)[:500]}\n```"
                )

        except httpx.TimeoutException:
            logger.error(f"[VCG-{attempt}] Timeout after {timeout}s")
            last_error_msg = "timeout"
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY * attempt)
                continue
            return (
                "❌ **Timeout** — API tidak merespons.\n"
                "Gambar mungkin terlalu besar. Coba lagi nanti.\n"
                "(Saldo tidak dipotong)"
            )

        except Exception as e:
            logger.error(f"[VCG-{attempt}] Unexpected: {type(e).__name__}: {e}")
            last_error_msg = f"{type(e).__name__}: {e}"
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY * attempt)
                continue
            return f"❌ **Error** — {type(e).__name__}: {e}"

    return (
        f"❌ **Gagal setelah {MAX_RETRIES} percobaan**\n"
        f"> {last_error_msg}\n\n"
        "(Saldo tidak dipotong — coba lagi nanti)"
    )

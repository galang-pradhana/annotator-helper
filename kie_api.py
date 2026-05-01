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


async def _call_kie_ai_internal(
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
                        return f"❌ **Kie.ai Error**: Server sedang bermasalah atau maintenance. Silakan gunakan /switch openrouter."
                    else:
                        if attempt < MAX_RETRIES:
                            wait = RETRY_DELAY * attempt
                            logger.warning(f"Server error {response.status_code}. Retry in {wait}s...")
                            await asyncio.sleep(wait)
                            continue
                        return f"❌ **Kie.ai Error**: Server sedang bermasalah atau maintenance. Silakan gunakan /switch openrouter."

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
                            return f"❌ **Kie.ai Error**: Server sedang bermasalah atau maintenance. Silakan gunakan /switch openrouter."
                        else:
                            # Server exception — retry 1x lalu bail
                            if attempt < MAX_RETRIES:
                                wait = RETRY_DELAY * attempt
                                logger.warning(f"Server exception. Retry in {wait}s...")
                                await asyncio.sleep(wait)
                                continue
                            return f"❌ **Kie.ai Error**: Server sedang bermasalah atau maintenance. Silakan gunakan /switch openrouter."

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
            return f"❌ **Kie.ai Error**: Server sedang bermasalah atau maintenance. Silakan gunakan /switch openrouter."

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

    # Semua retry habis - Fallback to OpenRouter
    return f"❌ **Kie.ai Error**: Semua percobaan gagal. {last_error_msg}. Silakan gunakan /switch openrouter."


async def _call_kie_ai_internal_multimodal(
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
                    if _is_maintenance_error(raw):
                        return f"❌ **Kie.ai Error**: Server sedang bermasalah atau maintenance. Silakan gunakan /switch openrouter."

                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(RETRY_DELAY * attempt)
                        continue
                    
                    return f"❌ **Kie.ai Error**: Server sedang bermasalah atau maintenance. Silakan gunakan /switch openrouter."

                data = response.json()

                if isinstance(data, dict):
                    api_code = data.get("code")
                    if api_code and str(api_code) != "200":
                        api_msg = data.get("msg") or data.get("message") or "Unknown"
                        logger.error(f"[VCG-{attempt}] Wrapped error {api_code}: {api_msg}")
                        last_error_msg = f"code {api_code}: {api_msg}"
                        if _is_maintenance_error(api_msg):
                            return f"❌ **Kie.ai Error**: Server sedang bermasalah atau maintenance. Silakan gunakan /switch openrouter."

                        if attempt < MAX_RETRIES:
                            await asyncio.sleep(RETRY_DELAY * attempt)
                            continue
                            
                        return f"❌ **Kie.ai Error**: Server sedang bermasalah atau maintenance. Silakan gunakan /switch openrouter."

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
            return f"❌ **Kie.ai Error**: Server sedang bermasalah atau maintenance. Silakan gunakan /switch openrouter."

        except Exception as e:
            logger.error(f"[VCG-{attempt}] Unexpected: {type(e).__name__}: {e}")
            last_error_msg = f"{type(e).__name__}: {e}"
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY * attempt)
                continue
            return f"❌ **Error** — {type(e).__name__}: {e}"

    # Semua retry habis - Fallback to OpenRouter
    logger.warning(f"VCG All retries exhausted for Kie.ai. Fallback to OpenRouter... Last error: {last_error_msg}")
    return await call_openrouter_api_multimodal(system_prompt, user_text, images_b64, model_name)


# ── OpenRouter Fallback ───────────────────────────────────────────────────────

def _map_to_openrouter_model(kie_model_name: str) -> str:
    """Memetakan nama model Kie.ai ke model OpenRouter sesuai preferensi user."""
    model = (kie_model_name or "").lower()
    
    # BASIC tier diarahkan ke Gemini 2.5 Flash Lite
    # Sangat hemat tapi penalaran jauh di atas Llama 3 8B gratisan.
    if "flash" in model:
        return "google/gemini-2.5-flash-lite"
        
    # PRO/PREMIUM tier diarahkan ke Grok Fast
    # Sesuai permintaan, fallback openrouter menggunakan Grok Fast agar lebih baik
    return "x-ai/grok-fast"

async def call_openrouter_api(system_prompt: str, user_input: str, model_name: str) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return "❌ **OpenRouter API Key tidak ditemukan di .env**"
        
    or_model = _map_to_openrouter_model(model_name)
    
    if "claude" in (model_name or "").lower():
        return "❌ **Model Claude sementara dinonaktifkan di fallback OpenRouter.**"

    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://kie.ai", # Fallback referer
        "X-OpenRouter-Title": "Annotator Pro",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": or_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    }
    
    logger.info(f"🔄 FALLBACK TO OPENROUTER | MODEL: {or_model} | PROMPT: {len(system_prompt)} chars")
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            if response.status_code != 200:
                return f"❌ **OpenRouter Error {response.status_code}**\n```\n{response.text[:500]}\n```"
                
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                reply = choices[0].get("message", {}).get("content", "")
                logger.info(f"✅ [OpenRouter] Response OK | {len(reply)} chars")
                return reply
            return f"⚠️ Format OpenRouter API tidak dikenali:\n```json\n{str(data)[:500]}\n```"
    except Exception as e:
        return f"❌ **OpenRouter Exception** — {type(e).__name__}: {e}"


async def call_openrouter_api_multimodal(system_prompt: str, user_text: str, images_b64: dict, model_name: str) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return "❌ **OpenRouter API Key tidak ditemukan di .env**"
        
    or_model = _map_to_openrouter_model(model_name)
    
    if "claude" in (model_name or "").lower():
        return "❌ **Model Claude sementara dinonaktifkan di fallback OpenRouter.**"

    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://kie.ai",
        "X-OpenRouter-Title": "Annotator Pro",
        "Content-Type": "application/json"
    }
    
    content_parts = []
    for label, b64_data in images_b64.items():
        content_parts.append({"type": "text", "text": f"**Gambar {label}:**"})
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}
        })
    content_parts.append({"type": "text", "text": user_text})
    
    payload = {
        "model": or_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_parts}
        ]
    }
    
    logger.info(f"🔄 VCG FALLBACK TO OPENROUTER | MODEL: {or_model} | IMAGES: {list(images_b64.keys())}")
    
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            if response.status_code != 200:
                return f"❌ **OpenRouter Error {response.status_code}**\n```\n{response.text[:500]}\n```"
                
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                reply = choices[0].get("message", {}).get("content", "")
                logger.info(f"✅ [VCG/OpenRouter] Response OK | {len(reply)} chars")
                return reply
            return f"⚠️ Format OpenRouter API tidak dikenali:\n```json\n{str(data)[:500]}\n```"
    except Exception as e:
        return f"❌ **OpenRouter Exception** — {type(e).__name__}: {e}"

# ── Router & Status ────────────────────────────────────────────────────────────

async def call_ai_engine(system_prompt: str, user_input: str, model_override: str = None) -> str:
    engine = os.environ.get("ACTIVE_ENGINE", "openrouter").lower()
    if engine == "openrouter":
        return await call_openrouter_api(system_prompt, user_input, model_override)
    else:
        return await _call_kie_ai_internal(system_prompt, user_input, model_override)

async def call_ai_engine_multimodal(system_prompt: str, user_text: str, images_b64: dict, model_override: str = None) -> str:
    engine = os.environ.get("ACTIVE_ENGINE", "openrouter").lower()
    if engine == "openrouter":
        return await call_openrouter_api_multimodal(system_prompt, user_text, images_b64, model_override)
    else:
        return await _call_kie_ai_internal_multimodal(system_prompt, user_text, images_b64, model_override)

async def check_engine_status() -> str:
    """Memeriksa status dari Kie.ai dan OpenRouter dengan melakukan request ringan."""
    status_report = "🔍 **Laporan Status Engine**\n\n"
    
    # Check Kie.ai
    status_report += "🟢 **Kie.ai:**\n"
    try:
        api_url = os.environ.get("KIE_API_URL", "https://api.kie.ai")
        # Kita coba hit endpoint models untuk cek koneksi
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{api_url.rstrip('/')}/v1/models")
            if resp.status_code == 200 or resp.status_code == 404 or resp.status_code == 401:
                # Setidaknya server merespons
                status_report += f"  • Server Reachable (HTTP {resp.status_code})\n"
            else:
                status_report += f"  • ⚠️ Error: HTTP {resp.status_code}\n"
    except Exception as e:
         status_report += f"  • ❌ Down: {type(e).__name__}\n"

    # Check OpenRouter
    status_report += "\n🔵 **OpenRouter:**\n"
    try:
        or_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not or_key:
            status_report += "  • ⚠️ API Key tidak ditemukan\n"
        else:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://openrouter.ai/api/v1/auth/key", 
                    headers={"Authorization": f"Bearer {or_key}"}
                )
                if resp.status_code == 200:
                    status_report += "  • ✅ API Key Valid\n"
                elif resp.status_code == 401:
                    status_report += "  • ❌ API Key Invalid (401)\n"
                else:
                    status_report += f"  • ⚠️ Error: HTTP {resp.status_code}\n"
    except Exception as e:
        status_report += f"  • ❌ Down: {type(e).__name__}\n"
        
    active = os.environ.get("ACTIVE_ENGINE", "openrouter").upper()
    status_report += f"\n📍 **Active Engine:** `{active}`"
    return status_report


async def test_ai_engine(tier: str = "BASIC") -> str:
    """Melakukan tes pengerjaan nyata ke engine yang aktif."""
    engine = os.environ.get("ACTIVE_ENGINE", "openrouter").lower()
    # Petakan tier ke model name yang biasa dipakai di bot
    model_name = "gemini-3-flash" if tier.upper() == "BASIC" else "gemini-3.1-pro"
    
    test_prompt = "Hi, this is a system health check. Please reply with 'READY' if you can hear me."
    
    logger.info(f"🧪 TESTING ENGINE: {engine.upper()} | TIER: {tier} | MODEL: {model_name}")
    
    try:
        if engine == "openrouter":
            resp = await call_openrouter_api("You are a helpful assistant.", test_prompt, model_name)
        else:
            resp = await _call_kie_ai_internal("You are a helpful assistant.", test_prompt, model_name)
        
        if resp.startswith(("❌", "⚠️")):
            return f"❌ **Test Gagal!**\n\n{resp}"
        
        return (
            f"✅ **Test Berhasil!**\n\n"
            f"📍 Engine: `{engine.upper()}`\n"
            f"💎 Tier: `{tier.upper()}`\n"
            f"🤖 AI Reply: `{resp.strip()}`\n\n"
            f"Sistem siap digunakan untuk tugas nyata."
        )
    except Exception as e:
        return f"❌ **Test Exception** — `{type(e).__name__}: {e}`"


"""
rag/embedder.py
---------------
Generate text embeddings untuk chunks guideline.

Strategy:
- Primary  : Google Generative AI embedding (text-embedding-004)
             → Gratis, 768 dimensi, cocok untuk dokumen teknis
- Fallback  : Simple TF-IDF-style hashing (no external dep)
             → Dipakai saat Google API tidak tersedia

Dimensi output: 768 (Google) atau 256 (fallback hash)
"""

import os
import math
import hashlib
import logging
import asyncio
from typing import Union

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
GOOGLE_EMBED_MODEL    = "gemini-embedding-001"   # Model aktif (text-embedding-004 deprecated)
EMBEDDING_DIM_GOOGLE   = 768    # Pakai outputDimensionality=768 via Matryoshka (full=3072)
                                 # 768 dipilih agar kompatibel dengan HNSW index (max 2000 dim)
EMBEDDING_DIM_FALLBACK = 256
EMBED_BATCH_SIZE       = 10    # Max texts per API call — lebih kecil dari limit Google untuk safety
EMBED_TIMEOUT          = 30   # Seconds per request


# ══════════════════════════════════════════════════════════════════════════════
# PRIMARY: Google text-embedding-004
# ══════════════════════════════════════════════════════════════════════════════

async def _embed_google_batch(texts: list[str], api_key: str) -> list[list[float]] | None:
    """
    Embed satu batch teks menggunakan Google Generative AI API.
    
    Endpoint: POST https://generativelanguage.googleapis.com/v1beta/models/
              text-embedding-004:batchEmbedContents
    
    Returns:
        List of embedding vectors, atau None jika gagal.
    """
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GOOGLE_EMBED_MODEL}:batchEmbedContents?key={api_key}"
    )
    
    requests_payload = [
        {
            "model": f"models/{GOOGLE_EMBED_MODEL}",
            "content": {"parts": [{"text": t}]},
            "taskType": "RETRIEVAL_DOCUMENT",
            "outputDimensionality": EMBEDDING_DIM_GOOGLE,
        }
        for t in texts
    ]
    
    try:
        async with httpx.AsyncClient(timeout=EMBED_TIMEOUT) as client:
            resp = await client.post(
                endpoint,
                json={"requests": requests_payload},
            )
        
        if resp.status_code != 200:
            logger.error(f"Google Embed API error {resp.status_code}: {resp.text[:300]}")
            return None
        
        data = resp.json()
        embeddings = data.get("embeddings", [])
        
        return [e["values"] for e in embeddings]
    
    except Exception as e:
        logger.error(f"Google Embed exception: {type(e).__name__}: {e}")
        return None


async def embed_texts_google(texts: list[str]) -> list[list[float]] | None:
    """
    Embed semua teks (dalam batch) menggunakan Google API.
    
    Returns:
        List of embedding vectors (float), atau None jika API tidak tersedia/gagal.
    """
    api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not api_key:
        logger.warning("GOOGLE_API_KEY tidak diset → skip Google embedding")
        return None
    
    all_embeddings = []
    
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        logger.info(f"Embedding batch {i//EMBED_BATCH_SIZE + 1}: {len(batch)} texts")
        
        result = await _embed_google_batch(batch, api_key)
        if result is None:
            logger.error(f"Batch {i//EMBED_BATCH_SIZE + 1} gagal → abort")
            return None
        
        all_embeddings.extend(result)
        
        # Rate limiting: jeda kecil antar batch
        if i + EMBED_BATCH_SIZE < len(texts):
            await asyncio.sleep(0.2)
    
    logger.info(f"✅ Google embedding selesai: {len(all_embeddings)} vectors (dim={EMBEDDING_DIM_GOOGLE})")
    return all_embeddings


# ══════════════════════════════════════════════════════════════════════════════
# QUERY EMBEDDING: untuk saat retrieval (task type berbeda)
# ══════════════════════════════════════════════════════════════════════════════

async def embed_query_google(query: str) -> list[float] | None:
    """
    Embed satu query string untuk similarity search.
    Menggunakan taskType RETRIEVAL_QUERY (berbeda dari DOCUMENT).
    """
    api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not api_key:
        return None
    
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GOOGLE_EMBED_MODEL}:embedContent?key={api_key}"
    )
    
    try:
        async with httpx.AsyncClient(timeout=EMBED_TIMEOUT) as client:
            resp = await client.post(
                endpoint,
                json={
                    "model": f"models/{GOOGLE_EMBED_MODEL}",
                    "content": {"parts": [{"text": query}]},
                    "taskType": "RETRIEVAL_QUERY",
                    "outputDimensionality": EMBEDDING_DIM_GOOGLE,
                }
            )
        
        if resp.status_code != 200:
            logger.error(f"Query embed error {resp.status_code}: {resp.text[:200]}")
            return None
        
        data = resp.json()
        return data.get("embedding", {}).get("values")
    
    except Exception as e:
        logger.error(f"Query embed exception: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# FALLBACK: Hash-based embedding (no external dependency)
# ══════════════════════════════════════════════════════════════════════════════

def _hash_embed_text(text: str, dim: int = EMBEDDING_DIM_FALLBACK) -> list[float]:
    """
    Generate pseudo-embedding menggunakan deterministic hashing.
    
    Ini BUKAN embedding semantik — hanya untuk fallback/testing ketika
    API tidak tersedia. Similarity search akan kurang akurat.
    """
    # Tokenize sederhana: split + lowercase
    tokens = text.lower().split()
    
    vector = [0.0] * dim
    
    for token in tokens:
        # Hash token → index + value
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        idx = h % dim
        # Nilai menggunakan bit berbeda dari hash
        val = ((h >> 16) & 0xFFFF) / 0xFFFF  # Normalisasi ke [0, 1]
        vector[idx] += val
    
    # L2 normalisasi
    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude > 0:
        vector = [v / magnitude for v in vector]
    
    return vector


def embed_texts_fallback(texts: list[str]) -> list[list[float]]:
    """Embed semua teks menggunakan hash fallback (synchronous)."""
    logger.warning(
        "⚠️ Menggunakan FALLBACK hash embedding. "
        "Set GOOGLE_API_KEY untuk semantic search yang akurat."
    )
    return [_hash_embed_text(t) for t in texts]


def embed_query_fallback(query: str) -> list[float]:
    """Embed satu query menggunakan hash fallback."""
    return _hash_embed_text(query)


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API: Auto-select best available embedder
# ══════════════════════════════════════════════════════════════════════════════

async def embed_texts(texts: list[str]) -> tuple[list[list[float]], int, str]:
    """
    Embed list of texts menggunakan metode terbaik yang tersedia.
    
    Returns:
        (embeddings, dimension, method_name)
        - embeddings : List of float vectors
        - dimension  : Dimensi tiap vector
        - method_name: "google" atau "fallback"
    """
    if not texts:
        return [], 0, "none"
    
    # Coba Google dulu
    google_result = await embed_texts_google(texts)
    if google_result and len(google_result) == len(texts):
        return google_result, EMBEDDING_DIM_GOOGLE, "google"
    
    # Fallback ke hash
    fallback_result = embed_texts_fallback(texts)
    return fallback_result, EMBEDDING_DIM_FALLBACK, "fallback"


async def embed_query(query: str) -> tuple[list[float], int, str]:
    """
    Embed satu query string.
    
    Returns:
        (embedding_vector, dimension, method_name)
    """
    # Coba Google query embedding
    google_result = await embed_query_google(query)
    if google_result:
        return google_result, EMBEDDING_DIM_GOOGLE, "google"
    
    # Fallback
    fallback_result = embed_query_fallback(query)
    return fallback_result, EMBEDDING_DIM_FALLBACK, "fallback"


def get_embedding_dim() -> int:
    """Return dimensi embedding yang akan digunakan (untuk setup tabel pgvector)."""
    if os.environ.get("GOOGLE_API_KEY", "").strip():
        return EMBEDDING_DIM_GOOGLE
    return EMBEDDING_DIM_FALLBACK

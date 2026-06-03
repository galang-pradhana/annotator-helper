"""
rag/retriever.py
----------------
Interface utama RAG pipeline untuk prompt_assembler.

Flow:
    query (str) + task_code
        → embed_query()           [embedder.py]
        → vector_store.search()   [vector_store.py]
        → format_context()        [format teks untuk prompt]
        → return context_str

Fungsi yang dipanggil dari prompt_assembler.py:
    - retrieve_guideline_context(query, task_code, top_k) → str
    - is_rag_ready() → bool
"""

import logging
from typing import Optional

from rag.embedder import embed_query
from rag import vector_store

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
DEFAULT_TOP_K           = 6
# Threshold berbeda tergantung metode embedding:
# - Google (semantic): 0.15 → diturunkan dari 0.25 agar query Bahasa Indonesia
#   terhadap dokumen Bahasa Inggris tetap ter-retrieve (perbedaan bahasa menurunkan
#   similarity secara artifisial meski kontennya relevan)
# - Fallback (hash)  : 0.05 → hash embedding menghasilkan similarity rendah (~0.05–0.12)
#   sehingga threshold harus diturunkan agar retrieval tidak selalu gagal
SIMILARITY_THRESHOLD_SEMANTIC  = 0.15
SIMILARITY_THRESHOLD_FALLBACK  = 0.05
MAX_CONTEXT_CHARS       = 6000   # Dinaikkan dari 4000 — top_k=6 butuh lebih banyak ruang


# ══════════════════════════════════════════════════════════════════════════════
# Format Context
# ══════════════════════════════════════════════════════════════════════════════

def _format_rag_context(chunks: list[dict]) -> str:
    """
    Format hasil retrieval menjadi blok teks yang siap diinjeksi ke prompt.
    
    Output format:
    ┌─────────────────────────────────────────────────────────┐
    │ === RELEVANT GUIDELINE CONTEXT (RAG) ===                │
    │                                                         │
    │ [1] Source: PR > Scoring Criteria (similarity: 0.87)   │
    │ ... chunk text ...                                      │
    │                                                         │
    │ [2] Source: PR > Preference Ranking Rules (0.79)       │
    │ ... chunk text ...                                      │
    └─────────────────────────────────────────────────────────┘
    """
    if not chunks:
        return ""
    
    lines = [
        "=" * 72,
        "RELEVANT GUIDELINE CONTEXT (retrieved via RAG)",
        "Gunakan konteks berikut sebagai GROUND TRUTH untuk evaluasi.",
        "=" * 72,
        "",
    ]
    
    total_chars = 0
    included = 0
    
    for i, chunk in enumerate(chunks, 1):
        chunk_text = chunk["chunk_text"]
        similarity  = chunk["similarity"]
        heading     = chunk["heading"]
        task        = chunk["task_code"]
        
        entry_header = f"[{i}] {task} › {heading} (relevance: {similarity:.0%})"
        entry = f"{entry_header}\n{'-' * len(entry_header)}\n{chunk_text}"
        
        # Pastikan tidak melebihi batas karakter
        if total_chars + len(entry) > MAX_CONTEXT_CHARS and included > 0:
            lines.append(f"... (+{len(chunks) - included} chunk lain tidak ditampilkan karena batas konteks)")
            break
        
        lines.append(entry)
        lines.append("")  # Blank line antar chunk
        total_chars += len(entry)
        included += 1
    
    lines.append("=" * 72)
    lines.append("END OF GUIDELINE CONTEXT")
    lines.append("=" * 72)
    
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# Main Retrieval Function
# ══════════════════════════════════════════════════════════════════════════════

async def retrieve_guideline_context(
    query: str,
    task_code: Optional[str] = None,
    top_k: int = DEFAULT_TOP_K,
) -> str:
    """
    Pipeline lengkap: embed query → search vector store → format context.
    Wrapper backward-compatible di atas retrieve_guideline_context_with_meta.
    
    Returns:
        String context siap diinjeksi ke prompt, atau "" jika tidak ada hasil.
    """
    result = await retrieve_guideline_context_with_meta(query, task_code, top_k)
    return result["text"]


async def retrieve_guideline_context_with_meta(
    query: str,
    task_code: Optional[str] = None,
    top_k: int = DEFAULT_TOP_K,
) -> dict:
    """
    Pipeline lengkap dengan metadata: embed query → search → format context.
    
    Strategi retrieval (bertingkat):
    1. Coba search dengan filter task_code + threshold normal
    2. Jika kosong, coba search tanpa filter task_code (cross-task fallback)
    3. Jika masih kosong, return empty
    
    Args:
        query     : Teks yang akan dicari kemiripannya dengan guideline.
        task_code : Filter ke task tertentu (e.g. "PR"). None = semua task.
        top_k     : Jumlah chunk yang diambil (default 6).
    
    Returns:
        dict dengan keys:
            "text"           : str  — context string untuk prompt
            "chunk_count"    : int  — jumlah chunk yang ditemukan
            "top_similarity" : float — similarity tertinggi (0.0 jika kosong)
            "source"         : str  — "guideline" | "cross_task" | "empty"
    """
    empty_result = {
        "text": "",
        "chunk_count": 0,
        "top_similarity": 0.0,
        "source": "empty",
    }
    
    if not query or not query.strip():
        logger.warning("retrieve_guideline_context_with_meta: query kosong")
        return empty_result
    
    # Step 1: Embed query
    query_vec, dim, method = await embed_query(query)
    if not query_vec:
        logger.error("Gagal embed query → skip RAG retrieval")
        return empty_result
    
    logger.info(f"🔍 Query embedded: dim={dim}, method={method}")
    
    # Step 2: Pilih threshold berdasarkan metode embedding
    sim_threshold = (
        SIMILARITY_THRESHOLD_SEMANTIC
        if method == "google"
        else SIMILARITY_THRESHOLD_FALLBACK
    )
    logger.info(f"🎯 Similarity threshold: {sim_threshold} (embed method: {method})")
    
    # Step 3a: Primary search — dengan filter task_code
    results = await vector_store.search(
        query_embedding=query_vec,
        task_code=task_code,
        top_k=top_k,
        similarity_threshold=sim_threshold,
    )
    source = "guideline"
    
    # Step 3b: Cross-task fallback — jika task-filtered search kosong
    if not results and task_code:
        logger.info(
            f"RAG: 0 hasil untuk task='{task_code}', coba cross-task fallback..."
        )
        results = await vector_store.search(
            query_embedding=query_vec,
            task_code=None,   # tanpa filter task
            top_k=top_k,
            similarity_threshold=sim_threshold,
        )
        source = "cross_task"
        if results:
            logger.info(
                f"RAG cross-task: {len(results)} chunk dari berbagai task "
                f"(top similarity: {results[0]['similarity']:.2f})"
            )
    
    if not results:
        logger.info(f"RAG: tidak ada chunk relevan untuk query '{query[:60]}...'")
        return empty_result
    
    logger.info(
        f"RAG: {len(results)} chunk ditemukan | source={source} | "
        f"top similarity: {results[0]['similarity']:.2f}"
    )
    
    # Step 4: Format
    context_str = _format_rag_context(results)
    
    return {
        "text": context_str,
        "chunk_count": len(results),
        "top_similarity": results[0]["similarity"] if results else 0.0,
        "source": source,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Health Check
# ══════════════════════════════════════════════════════════════════════════════

async def is_rag_ready() -> bool:
    """
    Cek apakah RAG vector store sudah siap dan berisi data.
    
    Dipanggil di awal bot startup untuk validasi.
    """
    try:
        s = await vector_store.stats()
        total = s.get("total_chunks", 0)
        if total == 0:
            logger.warning("⚠️ RAG vector store kosong! Jalankan: python rag/indexer.py")
            return False
        logger.info(f"✅ RAG ready: {total} chunks tersedia")
        return True
    except Exception as e:
        logger.error(f"RAG health check gagal: {e}")
        return False


async def get_rag_stats_summary() -> str:
    """Return human-readable stats string untuk admin /stats command."""
    try:
        s = await vector_store.stats()
        total = s.get("total_chunks", 0)
        by_task = s.get("by_task", {})
        by_method = s.get("embed_methods", {})
        
        task_lines = "\n".join(
            f"  • {task}: {count} chunks"
            for task, count in sorted(by_task.items())
        )
        method_lines = "\n".join(
            f"  • {m}: {c}"
            for m, c in by_method.items()
        )
        
        return (
            f"📚 **RAG Vector Store Stats**\n"
            f"Total chunks: **{total}**\n\n"
            f"Per task:\n{task_lines}\n\n"
            f"Embedding method:\n{method_lines}"
        )
    except Exception as e:
        return f"❌ RAG stats error: {e}"

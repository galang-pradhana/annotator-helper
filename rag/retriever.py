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
DEFAULT_TOP_K           = 5
# Threshold berbeda tergantung metode embedding:
# - Google (semantic): 0.25 → similarity cukup tinggi, akurat
# - Fallback (hash)  : 0.05 → hash embedding menghasilkan similarity rendah (~0.05–0.12)
#   sehingga threshold harus diturunkan agar retrieval tidak selalu gagal
SIMILARITY_THRESHOLD_SEMANTIC  = 0.25
SIMILARITY_THRESHOLD_FALLBACK  = 0.05
MAX_CONTEXT_CHARS       = 4000   # Batas total karakter konteks yang diinjeksi ke prompt


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
    
    Ini adalah fungsi UTAMA yang dipanggil dari prompt_assembler.py.
    
    Args:
        query     : Teks yang akan dicari kemiripannya dengan guideline.
                    Bisa berupa: task description, user input, atau keyword.
        task_code : Filter ke task tertentu (e.g. "PR"). None = semua task.
        top_k     : Jumlah chunk yang diambil.
    
    Returns:
        String context siap diinjeksi ke prompt, atau "" jika tidak ada hasil.
    
    Example:
        context = await retrieve_guideline_context(
            query="instruction following evaluation criteria scoring",
            task_code="PR",
            top_k=5,
        )
        # Masukkan ke prompt:
        # system_prompt = f"{context}\n\n{master_prompt}"
    """
    if not query or not query.strip():
        logger.warning("retrieve_guideline_context: query kosong")
        return ""
    
    # Step 1: Embed query
    query_vec, dim, method = await embed_query(query)
    if not query_vec:
        logger.error("Gagal embed query → skip RAG retrieval")
        return ""
    
    logger.info(f"🔍 Query embedded: dim={dim}, method={method}")
    
    # Step 2: Pilih threshold berdasarkan metode embedding
    # Hash fallback menghasilkan similarity rendah (~0.05–0.12), sehingga threshold
    # harus disesuaikan agar retrieval tidak selalu gagal.
    sim_threshold = (
        SIMILARITY_THRESHOLD_SEMANTIC
        if method == "google"
        else SIMILARITY_THRESHOLD_FALLBACK
    )
    logger.info(f"🎯 Similarity threshold: {sim_threshold} (embed method: {method})")
    
    # Step 3: Search
    results = await vector_store.search(
        query_embedding=query_vec,
        task_code=task_code,
        top_k=top_k,
        similarity_threshold=sim_threshold,
    )
    
    if not results:
        logger.info(f"RAG: tidak ada chunk relevan untuk query '{query[:60]}...'")
        return ""
    
    logger.info(
        f"RAG: {len(results)} chunk ditemukan | "
        f"top similarity: {results[0]['similarity']:.2f}"
    )
    
    # Step 4: Format
    context_str = _format_rag_context(results)
    
    return context_str


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

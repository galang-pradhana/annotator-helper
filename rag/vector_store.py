"""
rag/vector_store.py
-------------------
Simpan dan cari chunk embeddings di PostgreSQL dengan ekstensi pgvector.

Extends database yang sudah ada di project (asyncpg + SQLModel).

Schema baru (1 tabel):
    guideline_chunks
    ├── id           : SERIAL PRIMARY KEY
    ├── task_code    : VARCHAR (e.g. "PR", "AFM")
    ├── source_file  : VARCHAR
    ├── heading      : TEXT
    ├── chunk_index  : INTEGER
    ├── chunk_text   : TEXT
    ├── embedding    : VECTOR(768)   ← pgvector column
    ├── embed_method : VARCHAR       ← "google" atau "fallback"
    └── created_at   : TIMESTAMP

Operasi utama:
    - setup()           : Install pgvector + buat tabel
    - upsert_chunks()   : Insert/update chunks + embedding
    - search()          : Cosine similarity search
    - clear_task()      : Hapus semua chunks untuk 1 task
    - stats()           : Jumlah chunk per task
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional

import asyncpg
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
TABLE_NAME      = "guideline_chunks"
DEFAULT_TOP_K   = 5        # Jumlah chunk yang di-retrieve per query
MAX_TOP_K       = 10       # Batas maksimal top-k


# ══════════════════════════════════════════════════════════════════════════════
# Connection Helper
# ══════════════════════════════════════════════════════════════════════════════

async def _get_conn() -> asyncpg.Connection:
    """Buat satu connection ke PostgreSQL dari DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL", "")
    
    if not db_url:
        raise RuntimeError("DATABASE_URL tidak diset di .env")
    
    # asyncpg tidak support prefix postgresql+asyncpg://
    # Normalize URL jika datang dari SQLAlchemy format
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    return await asyncpg.connect(db_url, statement_cache_size=0)


# ══════════════════════════════════════════════════════════════════════════════
# Setup: Install pgvector + Create Table
# ══════════════════════════════════════════════════════════════════════════════

async def setup(embedding_dim: int = 768) -> bool:
    """
    Install ekstensi pgvector dan buat tabel guideline_chunks.
    
    Aman dipanggil berkali-kali (idempotent).
    
    Args:
        embedding_dim: Dimensi vector sesuai model embedding yang dipakai.
    
    Returns:
        True jika berhasil, False jika gagal.
    """
    conn = None
    try:
        conn = await _get_conn()
        
        # 1. Install pgvector extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        logger.info("✅ pgvector extension: OK")
        
        # 2. Buat tabel (jika belum ada)
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id           SERIAL PRIMARY KEY,
                task_code    VARCHAR(50)  NOT NULL,
                source_file  VARCHAR(500) NOT NULL,
                heading      TEXT         NOT NULL,
                chunk_index  INTEGER      NOT NULL,
                chunk_text   TEXT         NOT NULL,
                embedding    VECTOR({embedding_dim}),
                embed_method VARCHAR(20)  DEFAULT 'unknown',
                created_at   TIMESTAMP    DEFAULT NOW(),
                
                -- Unique constraint: satu chunk per (source_file, chunk_index)
                UNIQUE (source_file, chunk_index)
            );
        """)
        logger.info(f"✅ Tabel '{TABLE_NAME}' siap (dim={embedding_dim})")
        
        # 3. Buat index untuk cosine similarity
        #    HNSW: support semua dimensi (termasuk 3072 dari gemini-embedding-001),
        #    lebih akurat dari IVFFlat, tersedia di pgvector >= 0.5.0 (Supabase sudah support)
        #    IVFFlat tidak bisa dipakai untuk dim > 2000.
        try:
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {TABLE_NAME}_embedding_idx
                ON {TABLE_NAME}
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
            """)
            logger.info("✅ HNSW index: OK")
        except Exception as idx_err:
            # Sequential scan tetap berjalan dengan benar tanpa index
            logger.warning(f"Index creation skip (sequential scan aktif): {idx_err}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Setup vector store gagal: {type(e).__name__}: {e}")
        logger.error(
            "Pastikan PostgreSQL sudah install pgvector:\n"
            "  sudo apt install postgresql-<ver>-pgvector\n"
            "  atau: CREATE EXTENSION vector;"
        )
        return False
    
    finally:
        if conn:
            await conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# Upsert Chunks
# ══════════════════════════════════════════════════════════════════════════════

async def upsert_chunks(
    chunks_with_embeddings: list[dict],
    embed_method: str = "google",
) -> int:
    """
    Insert atau update chunks ke tabel guideline_chunks.
    
    Args:
        chunks_with_embeddings: List of dict dengan keys:
            {
                "text": str,
                "task_code": str,
                "source_file": str,
                "heading": str,
                "chunk_index": int,
                "embedding": list[float],
            }
        embed_method: Nama metode embedding ("google" atau "fallback")
    
    Returns:
        Jumlah rows yang berhasil di-upsert.
    """
    if not chunks_with_embeddings:
        return 0
    
    conn = None
    try:
        conn = await _get_conn()
        
        # Register pgvector type handler
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        upserted = 0
        
        for chunk_data in chunks_with_embeddings:
            embedding = chunk_data.get("embedding", [])
            if not embedding:
                logger.warning(f"Skip chunk tanpa embedding: {chunk_data.get('heading')}")
                continue
            
            # Format vector sebagai string PostgreSQL: '[0.1, 0.2, ...]'
            embedding_str = "[" + ",".join(f"{v:.6f}" for v in embedding) + "]"
            
            await conn.execute(f"""
                INSERT INTO {TABLE_NAME}
                    (task_code, source_file, heading, chunk_index,
                     chunk_text, embedding, embed_method, created_at)
                VALUES
                    ($1, $2, $3, $4, $5, $6::vector, $7, $8)
                ON CONFLICT (source_file, chunk_index)
                DO UPDATE SET
                    task_code    = EXCLUDED.task_code,
                    heading      = EXCLUDED.heading,
                    chunk_text   = EXCLUDED.chunk_text,
                    embedding    = EXCLUDED.embedding,
                    embed_method = EXCLUDED.embed_method,
                    created_at   = EXCLUDED.created_at;
            """,
                chunk_data["task_code"],
                chunk_data["source_file"],
                chunk_data["heading"],
                chunk_data["chunk_index"],
                chunk_data["text"],
                embedding_str,
                embed_method,
                datetime.now(timezone.utc).replace(tzinfo=None),
            )
            upserted += 1
        
        logger.info(f"✅ Upserted {upserted}/{len(chunks_with_embeddings)} chunks ke DB")
        return upserted
    
    except Exception as e:
        logger.error(f"❌ Upsert error: {type(e).__name__}: {e}")
        raise
    
    finally:
        if conn:
            await conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# Search (Cosine Similarity)
# ══════════════════════════════════════════════════════════════════════════════

async def search(
    query_embedding: list[float],
    task_code: Optional[str] = None,
    top_k: int = DEFAULT_TOP_K,
    similarity_threshold: float = 0.3,
) -> list[dict]:
    """
    Cari chunk paling relevan menggunakan cosine similarity.
    
    Args:
        query_embedding     : Vector embedding dari query user
        task_code           : Filter berdasarkan task (None = semua task)
        top_k               : Jumlah chunk yang dikembalikan
        similarity_threshold: Minimal similarity score (0-1), buang yang di bawah ini
    
    Returns:
        List of dict sorted by similarity (highest first):
        [
            {
                "chunk_text": str,
                "task_code": str,
                "heading": str,
                "source_file": str,
                "similarity": float,  # 0.0 - 1.0
            },
            ...
        ]
    """
    if not query_embedding:
        return []
    
    top_k = min(max(1, top_k), MAX_TOP_K)
    
    conn = None
    try:
        conn = await _get_conn()
        
        embedding_str = "[" + ",".join(f"{v:.6f}" for v in query_embedding) + "]"
        
        # Cosine similarity = 1 - cosine_distance
        # pgvector: <=> = cosine distance (lower = more similar)
        # Kita convert ke similarity: 1 - distance
        
        if task_code:
            rows = await conn.fetch(f"""
                SELECT
                    chunk_text,
                    task_code,
                    heading,
                    source_file,
                    1 - (embedding <=> $1::vector) AS similarity
                FROM {TABLE_NAME}
                WHERE task_code = $2
                  AND 1 - (embedding <=> $1::vector) >= $3
                ORDER BY embedding <=> $1::vector
                LIMIT $4;
            """, embedding_str, task_code, similarity_threshold, top_k)
        else:
            rows = await conn.fetch(f"""
                SELECT
                    chunk_text,
                    task_code,
                    heading,
                    source_file,
                    1 - (embedding <=> $1::vector) AS similarity
                FROM {TABLE_NAME}
                WHERE 1 - (embedding <=> $1::vector) >= $2
                ORDER BY embedding <=> $1::vector
                LIMIT $3;
            """, embedding_str, similarity_threshold, top_k)
        
        results = [
            {
                "chunk_text": row["chunk_text"],
                "task_code": row["task_code"],
                "heading": row["heading"],
                "source_file": row["source_file"],
                "similarity": float(row["similarity"]),
            }
            for row in rows
        ]
        
        logger.info(
            f"🔍 Search selesai: {len(results)} chunk relevan "
            f"(task={task_code or 'all'}, top_k={top_k})"
        )
        return results
    
    except Exception as e:
        logger.error(f"❌ Search error: {type(e).__name__}: {e}")
        return []
    
    finally:
        if conn:
            await conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# Utility
# ══════════════════════════════════════════════════════════════════════════════

async def clear_task(task_code: str) -> int:
    """Hapus semua chunks untuk satu task. Berguna saat re-index."""
    conn = None
    try:
        conn = await _get_conn()
        result = await conn.execute(
            f"DELETE FROM {TABLE_NAME} WHERE task_code = $1;",
            task_code
        )
        count = int(result.split()[-1])
        logger.info(f"🗑️ Deleted {count} chunks untuk task '{task_code}'")
        return count
    except Exception as e:
        logger.error(f"clear_task error: {e}")
        return 0
    finally:
        if conn:
            await conn.close()


async def clear_all() -> int:
    """Hapus semua chunks dan drop table (full re-index). Gunakan dengan hati-hati!"""
    conn = None
    try:
        conn = await _get_conn()
        # Dapatkan jumlah baris sebelum di-drop
        count = 0
        try:
            count_res = await conn.fetchval(f"SELECT COUNT(*) FROM {TABLE_NAME};")
            count = count_res or 0
        except Exception:
            pass
            
        await conn.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
        logger.info(f"🗑️ Dropped table '{TABLE_NAME}' (berisi {count} chunks)")
        return count
    except Exception as e:
        logger.error(f"clear_all error: {e}")
        return 0
    finally:
        if conn:
            await conn.close()


async def stats() -> dict:
    """
    Statistik isi vector store.
    
    Returns:
        {
            "total_chunks": int,
            "by_task": {"PR": 42, "AFM": 38, ...},
            "embed_methods": {"google": 80, "fallback": 0},
        }
    """
    conn = None
    try:
        conn = await _get_conn()
        
        total_row = await conn.fetchrow(f"SELECT COUNT(*) as cnt FROM {TABLE_NAME};")
        total = total_row["cnt"] if total_row else 0
        
        task_rows = await conn.fetch(
            f"SELECT task_code, COUNT(*) as cnt FROM {TABLE_NAME} GROUP BY task_code ORDER BY cnt DESC;"
        )
        by_task = {row["task_code"]: row["cnt"] for row in task_rows}
        
        method_rows = await conn.fetch(
            f"SELECT embed_method, COUNT(*) as cnt FROM {TABLE_NAME} GROUP BY embed_method;"
        )
        by_method = {row["embed_method"]: row["cnt"] for row in method_rows}
        
        return {
            "total_chunks": total,
            "by_task": by_task,
            "embed_methods": by_method,
        }
    
    except Exception as e:
        logger.error(f"stats error: {e}")
        return {"total_chunks": 0, "by_task": {}, "embed_methods": {}}
    
    finally:
        if conn:
            await conn.close()

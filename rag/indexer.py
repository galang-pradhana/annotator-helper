"""
rag/indexer.py
--------------
Script untuk index semua file guideline (.md) ke PostgreSQL pgvector.

Jalankan sekali (atau setiap kali guideline diupdate):
    python -m rag.indexer
    
    # atau dengan opsi:
    python -m rag.indexer --task PR          # Index satu task saja
    python -m rag.indexer --clear-all        # Hapus semua lalu re-index
    python -m rag.indexer --stats            # Lihat statistik tanpa indexing

Flow:
    1. Baca semua .md dari assets/guidelines/ (via ASSET_CONFIGS)
    2. Chunk setiap file
    3. Embed semua chunks (batch, Google API)
    4. Upsert ke PostgreSQL pgvector
"""

import asyncio
import argparse
import logging
import os
import sys

# Tambahkan root project ke sys.path agar bisa import dari parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from rag.chunker import chunk_all_guidelines, chunk_markdown_file
from rag.embedder import embed_texts, get_embedding_dim
from rag import vector_store
from prompt_assembler import ASSET_CONFIGS, ASSETS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("rag.indexer")


async def index_all(clear_first: bool = False, task_filter: str = None):
    """
    Main indexing function.
    
    Args:
        clear_first  : Hapus semua data lama sebelum index ulang
        task_filter  : Jika diisi, hanya index task ini (e.g. "PR")
    """
    print("\n" + "=" * 60)
    print("🚀 ANNOTATOR PRO — RAG INDEXER")
    print("=" * 60)
    
    # ── Step 0: Clear jika diminta ────────────────────────────────────────
    if clear_first:
        print("\n[!] Menghapus semua data lama (termasuk tabel database)...")
        deleted = await vector_store.clear_all()
        print(f"    ✅ Clear selesai")
        
    # ── Step 0.5: Setup vector store ────────────────────────────────────────
    print("\n[1/4] Setup pgvector database...")
    dim = get_embedding_dim()
    print(f"      Embedding dimension: {dim}")
    
    ok = await vector_store.setup(embedding_dim=dim)
    if not ok:
        print("❌ Setup gagal. Periksa DATABASE_URL dan pgvector installation.")
        print("\nInstall pgvector:")
        print("  Ubuntu: sudo apt install postgresql-16-pgvector")
        print("  Docker: gunakan image pgvector/pgvector:pg16")
        sys.exit(1)
    print("      ✅ Database siap")
    
    # ── Step 1: Chunk semua guidelines ────────────────────────────────────
    print("\n[2/4] Chunking guideline files...")
    
    # Filter ASSET_CONFIGS jika ada task_filter
    configs_to_use = ASSET_CONFIGS
    if task_filter:
        task_upper = task_filter.upper()
        configs_to_use = {
            k: v for k, v in ASSET_CONFIGS.items()
            if k.upper() == task_upper or k.upper().startswith(task_upper)
        }
        if not configs_to_use:
            print(f"❌ Task '{task_filter}' tidak ditemukan di ASSET_CONFIGS")
            print(f"   Available: {list(ASSET_CONFIGS.keys())}")
            sys.exit(1)
        print(f"      Filter: hanya task {list(configs_to_use.keys())}")
    
    all_chunks = chunk_all_guidelines(ASSETS_DIR, configs_to_use)
    
    if not all_chunks:
        print("⚠️ Tidak ada chunk yang dihasilkan. Periksa folder assets/guidelines/")
        sys.exit(1)
    
    print(f"      ✅ {len(all_chunks)} chunks dari {len(configs_to_use)} task configs")
    
    # Print breakdown per task
    by_task = {}
    for c in all_chunks:
        by_task[c.task_code] = by_task.get(c.task_code, 0) + 1
    for task, count in sorted(by_task.items()):
        print(f"         • {task}: {count} chunks")
    
    # ── Step 2 & 3: Embed & Upsert in Batches ──────────────────────────────
    print("\n[3/4 & 4/4] Generating embeddings & saving ke PostgreSQL (Batched)...")
    
    batch_size = 10
    total_upserted = 0
    actual_dim = dim
    method = "unknown"
    
    for i in range(0, len(all_chunks), batch_size):
        print(f"      Memproses batch {i//batch_size + 1} (chunks {i} - {min(i+batch_size, len(all_chunks))})...")
        chunk_batch = all_chunks[i : i + batch_size]
        texts_batch = [c.text for c in chunk_batch]
        
        embeddings_batch, current_dim, current_method = await embed_texts(texts_batch)
        actual_dim = current_dim
        method = current_method
        
        if len(embeddings_batch) != len(chunk_batch):
            print(f"❌ Jumlah embedding batch ({len(embeddings_batch)}) tidak match chunks ({len(chunk_batch)})")
            continue
            
        if method == "fallback" and i == 0:
            print("      ⚠️  PERINGATAN: Menggunakan hash fallback!")
            print("         Set GOOGLE_API_KEY di .env untuk semantic search yang akurat.")
            
        # Dim check: jika actual_dim berbeda dengan setup, perlu re-setup pada batch pertama
        if i == 0 and actual_dim != dim:
            print(f"\n⚠️  Dimensi berubah: setup={dim}, actual={actual_dim}")
            print("   Re-setup tabel dengan dimensi baru...")
            await vector_store.clear_all()
            ok = await vector_store.setup(embedding_dim=actual_dim)
            if not ok:
                print("❌ Re-setup gagal")
                sys.exit(1)
                
        chunks_with_embeddings = []
        for chunk, embedding in zip(chunk_batch, embeddings_batch):
            d = chunk.to_dict()
            d["embedding"] = embedding
            chunks_with_embeddings.append(d)
            
        upserted = await vector_store.upsert_chunks(chunks_with_embeddings, embed_method=method)
        total_upserted += upserted
        
        # Beri jeda 1 detik per batch untuk mencegah CPU overload/laptop freeze
        await asyncio.sleep(1)
        
    print(f"\n      ✅ {total_upserted} chunks tersimpan ke database")
    
    # ── Summary ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊 RINGKASAN INDEXING")
    print("=" * 60)
    
    stats = await vector_store.stats()
    print(f"Total chunks di DB : {stats['total_chunks']}")
    print(f"Embedding method   : {method} (dim={actual_dim})")
    print(f"\nPer task:")
    for task, count in sorted(stats.get("by_task", {}).items()):
        print(f"  • {task}: {count} chunks")
    
    print("\n✅ Indexing selesai! RAG pipeline siap digunakan.")
    print("\nNext step: Restart bot atau test dengan:")
    print("  python -m rag.indexer --stats")
    print("=" * 60 + "\n")


async def show_stats():
    """Tampilkan statistik vector store tanpa indexing."""
    print("\n📊 RAG Vector Store Stats\n")
    stats = await vector_store.stats()
    
    if stats["total_chunks"] == 0:
        print("⚠️  Vector store kosong. Jalankan indexer dulu:")
        print("   python -m rag.indexer")
        return
    
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"\nPer task:")
    for task, count in sorted(stats.get("by_task", {}).items()):
        print(f"  • {task}: {count} chunks")
    print(f"\nEmbedding methods:")
    for method, count in stats.get("embed_methods", {}).items():
        print(f"  • {method}: {count}")
    print()


def parse_args():
    parser = argparse.ArgumentParser(
        description="RAG Indexer untuk Annotator Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python -m rag.indexer                    # Index semua guidelines
  python -m rag.indexer --task PR          # Index task PR saja
  python -m rag.indexer --clear-all        # Hapus semua lalu re-index
  python -m rag.indexer --stats            # Lihat statistik
        """
    )
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        help="Filter task tertentu (e.g. PR, AFM, CYU)"
    )
    parser.add_argument(
        "--clear-all",
        action="store_true",
        help="Hapus semua data lama sebelum index ulang"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Hanya tampilkan statistik, tanpa indexing"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    if args.stats:
        asyncio.run(show_stats())
    else:
        asyncio.run(index_all(
            clear_first=args.clear_all,
            task_filter=args.task,
        ))

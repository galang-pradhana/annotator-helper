"""
rag/
----
RAG (Retrieval-Augmented Generation) pipeline untuk Annotator Pro.

Komponen:
    chunker.py      — Potong .md guideline jadi chunks
    embedder.py     — Generate embeddings (Google / fallback hash)
    vector_store.py — Simpan & cari di PostgreSQL pgvector
    retriever.py    — Interface utama: query → context string
    indexer.py      — Script CLI untuk index semua guidelines
"""

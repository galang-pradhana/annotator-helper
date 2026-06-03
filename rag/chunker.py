"""
rag/chunker.py
--------------
Memotong konten .md guideline menjadi chunks yang siap di-embed.

Strategy chunking:
- Split berdasarkan heading Markdown (##, ###) → semantic chunking
- Fallback ke fixed-size (500 token) jika section terlalu panjang
- Setiap chunk menyimpan metadata: task_code, source_file, heading, chunk_index
"""

import re
import os
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
MAX_CHUNK_CHARS = 1500   # ~375 tokens (1 token ≈ 4 chars)
MIN_CHUNK_CHARS = 80     # Abaikan chunk terlalu pendek (misal: heading kosong)
OVERLAP_CHARS   = 250    # Dinaikkan dari 150 agar konteks tidak terpotong


@dataclass
class Chunk:
    """Satu unit teks yang siap di-embed dan disimpan ke vector store."""
    text: str
    task_code: str        # e.g. "PR", "AFM", "CYU"
    source_file: str      # e.g. "assets/guidelines/pr_preference_ranking.md"
    heading: str          # Heading terdekat dari chunk ini
    chunk_index: int      # Urutan chunk dalam satu file
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "task_code": self.task_code,
            "source_file": self.source_file,
            "heading": self.heading,
            "chunk_index": self.chunk_index,
            **self.metadata,
        }


def _split_by_headings(content: str) -> list[tuple[str, str]]:
    """
    Split konten markdown berdasarkan heading (## atau ###).
    
    Returns:
        List of (heading, section_text) tuples.
    """
    # Pattern: baris yang dimulai dengan ## atau ###
    heading_pattern = re.compile(r'^(#{1,3}\s+.+)$', re.MULTILINE)
    
    sections = []
    last_heading = "Introduction"
    last_pos = 0
    
    for match in heading_pattern.finditer(content):
        # Ambil teks sebelum heading ini
        section_text = content[last_pos:match.start()].strip()
        if section_text and len(section_text) >= MIN_CHUNK_CHARS:
            sections.append((last_heading, section_text))
        
        last_heading = match.group(0).lstrip('#').strip()
        last_pos = match.end()
    
    # Section terakhir setelah heading terakhir
    remaining = content[last_pos:].strip()
    if remaining and len(remaining) >= MIN_CHUNK_CHARS:
        sections.append((last_heading, remaining))
    
    # Jika tidak ada heading sama sekali → treat seluruh file sebagai satu section
    if not sections and len(content.strip()) >= MIN_CHUNK_CHARS:
        sections.append(("Full Document", content.strip()))
    
    return sections


def _split_long_section(heading: str, text: str) -> list[tuple[str, str]]:
    """
    Split section yang terlalu panjang (> MAX_CHUNK_CHARS) menjadi sub-chunks.
    Menggunakan fixed-size dengan overlap.
    """
    if len(text) <= MAX_CHUNK_CHARS:
        return [(heading, text)]
    
    sub_chunks = []
    start = 0
    part = 1
    
    while start < len(text):
        end = start + MAX_CHUNK_CHARS
        if end >= len(text):
            chunk_text = text[start:]
            sub_chunks.append((f"{heading} (part {part})", chunk_text.strip()))
            break
        
        chunk_text = text[start:end]
        
        # Guard: Jangan memotong di tengah bullet list jika memungkinkan.
        # Kita lebih suka memotong di '\n\n', lalu sebelum list marker ('\n- ', '\n* ', '\n1. '), baru '\n'.
        if end < len(text):
            found_cut = False
            for sep in ['\n\n', '\n- ', '\n* ', '\n1. ', '\n', '. ', ' ']:
                idx = chunk_text.rfind(sep)
                if idx > MAX_CHUNK_CHARS * 0.6:  # Minimal 60% terisi
                    # Jika pemisah adalah list marker, kita potong SEBELUM marker tersebut
                    # agar marker utuh di chunk berikutnya (overlap akan menyertakannya).
                    if sep in ['\n- ', '\n* ', '\n1. ']:
                        chunk_text = chunk_text[:idx + 1] # Potong tepat di \n
                    else:
                        chunk_text = chunk_text[:idx + len(sep)]
                    found_cut = True
                    break
            
            # Jika tidak menemukan titik potong yang baik, paksa potong di end
            if not found_cut:
                chunk_text = text[start:end]
        
        sub_chunks.append((f"{heading} (part {part})", chunk_text.strip()))
        
        # Next start dengan overlap
        start += len(chunk_text) - OVERLAP_CHARS
        part += 1
    
    return sub_chunks


def chunk_markdown_file(
    filepath: str,
    task_code: str,
) -> list[Chunk]:
    """
    Baca file .md dan potong menjadi list of Chunk.
    
    Args:
        filepath:  Path absolut ke file .md
        task_code: Kode task (PR, AFM, CYU, dll) untuk metadata
    
    Returns:
        List of Chunk objects, siap untuk di-embed.
    """
    if not os.path.isfile(filepath):
        logger.warning(f"File tidak ditemukan: {filepath}")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if not content.strip():
        logger.warning(f"File kosong: {filepath}")
        return []
    
    # Normalisasi: hapus terlalu banyak blank lines
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    
    # Step 1: Split berdasarkan heading
    sections = _split_by_headings(content)
    
    # Step 2: Split section panjang
    all_sections = []
    for heading, text in sections:
        sub = _split_long_section(heading, text)
        all_sections.extend(sub)
    
    # Step 3: Bungkus jadi Chunk objects
    chunks = []
    rel_path = os.path.relpath(filepath)
    
    for idx, (heading, text) in enumerate(all_sections):
        if len(text.strip()) < MIN_CHUNK_CHARS:
            continue
        
        # Prefix setiap chunk dengan heading-nya untuk konteks saat retrieval
        chunk_text = f"[{task_code}] {heading}\n\n{text.strip()}"
        
        chunks.append(Chunk(
            text=chunk_text,
            task_code=task_code,
            source_file=rel_path,
            heading=heading,
            chunk_index=idx,
            metadata={
                "char_count": len(chunk_text),
                "filename": os.path.basename(filepath),
            }
        ))
    
    logger.info(
        f"✅ Chunked: {os.path.basename(filepath)} → {len(chunks)} chunks "
        f"(task={task_code})"
    )
    return chunks


def chunk_all_guidelines(assets_dir: str, asset_configs: dict) -> list[Chunk]:
    """
    Loop semua task code dan chunk semua file guidelines-nya.
    Mendukung key "supplements" (list of supplementary files per task).
    
    Args:
        assets_dir:    Path ke folder assets/
        asset_configs: Dict ASSET_CONFIGS dari prompt_assembler.py
    
    Returns:
        Flat list of all Chunk objects dari semua task.
    """
    all_chunks = []
    seen_files = set()  # Hindari proses file yang sama 2x (alias task)
    
    for task_code, config in asset_configs.items():
        # ── 1. File guidelines utama ────────────────────────────────────────
        guideline_rel = config.get("guidelines", "")
        if not guideline_rel:
            continue
        
        filepath = os.path.join(assets_dir, guideline_rel)
        abs_path = os.path.abspath(filepath)
        
        if abs_path in seen_files:
            logger.debug(f"Skip duplicate: {abs_path}")
        else:
            seen_files.add(abs_path)
            chunks = chunk_markdown_file(abs_path, task_code)
            all_chunks.extend(chunks)
        
        # ── 2. File supplement tambahan (opsional) ──────────────────────────
        supplement_rels = config.get("supplements", [])
        for supp_rel in supplement_rels:
            supp_path = os.path.join(assets_dir, supp_rel)
            supp_abs  = os.path.abspath(supp_path)
            
            if not os.path.isfile(supp_abs):
                # File belum ada — skip tanpa error (akan aktif saat file ditaruh)
                logger.debug(f"Supplement belum ada, skip: {supp_abs}")
                continue
            
            if supp_abs in seen_files:
                logger.debug(f"Skip duplicate supplement: {supp_abs}")
                continue
            
            seen_files.add(supp_abs)
            supp_chunks = chunk_markdown_file(supp_abs, task_code)
            all_chunks.extend(supp_chunks)
            logger.info(f"📎 Supplement loaded: {os.path.basename(supp_abs)} → {len(supp_chunks)} chunks")
    
    logger.info(
        f"📦 Total chunks dari semua guidelines: {len(all_chunks)} "
        f"dari {len(seen_files)} file unik"
    )
    return all_chunks

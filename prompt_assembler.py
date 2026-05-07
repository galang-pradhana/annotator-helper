"""
prompt_assembler_v2.py
----------------------
OPTIMIZED VERSION — Senior Annotator & Prompt Engineer Review

Perubahan dari v1:
1. Urutan block prompt dioptimalkan: Role → Brain → Interface → Output Contract → Execute → Edge Cases → Language Anchor
2. Output Contract yang eksplisit (template wajib diikuti AI)
3. Dynamic Language Anchor per bahasa target
4. Dynamic Self-Audit Checklist per task_code
5. Pre-evaluation audit section
6. Backward compatible dengan assemble_evaluator_prompt() lama

Cara migrasi:
  Ganti import di bot.py:
  FROM: from prompt_assembler import assemble_evaluator_prompt
  TO:   from prompt_assembler_v2 import assemble_evaluator_prompt
"""

import os
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# ── Mapping bahasa: kode → (nama lengkap, ISO 639-1) ─────────────────────
LANGUAGE_MAP: dict[str, tuple[str, str]] = {
    "TH": ("Bahasa Thailand", "th"),
    "JA": ("Bahasa Jepang", "ja"),
    "EN": ("Bahasa Inggris", "en"),
    "ID": ("Bahasa Indonesia", "id"),
    "KO": ("Bahasa Korea", "ko"),
    "MS": ("Bahasa Malaysia", "ms"),
    "VI": ("Bahasa Vietnam", "vi"),
    "ZH": ("Bahasa Mandarin", "zh"),
    "AR": ("Bahasa Arab", "ar"),
}

# ── Mapping Task → Asset Paths ─────────────────────────────────────────────
ASSET_CONFIGS = {
    "PR": {
        "guidelines": "guidelines/pr_preference_ranking.md",
        "forms": "forms/pr_forms.md",
        "prompts": "prompts/pr_prompt_instructions.md",
        "inputs": "inputs/pr_inputs.md",
    },
    "AFM": {
        "guidelines": "guidelines/afm_safety_guide.md",
        "forms": "forms/afm_safety_guide_forms.md",
        "prompts": "prompts/afm_safety_guide_instructions.md",
        "inputs": "inputs/afm_safety_guide_inputs.md",
    },
    "TC_MESSAGE_REPLY": {
        "guidelines": "guidelines/tc_message_reply.md",
        "forms": "forms/tc_message_reply_forms.md",
        "prompts": "prompts/tc_message_reply_instructions.md",
        "inputs": "inputs/tc_message_reply_inputs.md",
    },
    "TC_PROOFREADING": {
        "guidelines": "guidelines/tc_proofreading.md",
        "forms": "forms/tc_proofreading_forms.md",
        "prompts": "prompts/tc_proofreading_instructions.md",
        "inputs": "inputs/tc_proofreading_inputs.md",
    },
    "CYU": {
        "guidelines": "guidelines/cyu_website_topic.md",
        "forms": "forms/cyu_website_topic_forms.md",
        "prompts": "prompts/cyu_website_topic_instructions.md",
        "inputs": "inputs/cyu_website_topic_inputs.md",
    },
    "CYU_TOPLINE_SUMMARIZATION": {
        "guidelines": "guidelines/cyu_topline_summarization.md",
        "forms": "forms/cyu_topline_summarization_forms.md",
        "prompts": "prompts/cyu_topline_summarization_instructions.md",
        "inputs": "inputs/cyu_topline_summarization_inputs.md",
    },
    "CYU_WEBSITE_TOPIC": {
        "guidelines": "guidelines/cyu_website_topic.md",
        "forms": "forms/cyu_website_topic_forms.md",
        "prompts": "prompts/cyu_website_topic_instructions.md",
        "inputs": "inputs/cyu_website_topic_inputs.md",
    },
    "VCG_ADM_BASE_CREATION": {
        "guidelines": "guidelines/vcg_adm_creation_or_base_creation_model.md",
        "forms": "forms/vcg_adm_or_base_creation_model_forms.md",
        "prompts": "prompts/vcg_adm_or_base_creation_model_instructions.md",
        "inputs": "inputs/vcg_adm_or_base_creation_model_inputs.md",
    },
    "VCG_BACKGROUND_MESSAGE": {
        "guidelines": "guidelines/vcg_background_message.md",
        "forms": "forms/vcg_background_message_forms.md",
        "prompts": "prompts/vcg_background_message_instructions.md",
        "inputs": "inputs/vcg_background_message_inputs.md",
    },
    "VCG_EDIT_MODEL": {
        "guidelines": "guidelines/vcg_edit_model.md",
        "forms": "forms/vcg_edit_model_forms.md",
        "prompts": "prompts/vcg_edit_model_instructions.md",
        "inputs": "inputs/vcg_edit_model_inputs.md",
    },
    "VCG_PROMPT_REWRITE": {
        "guidelines": "guidelines/vcg_prompt_rewrite_text_to_image.md",
        "forms": "forms/vcg_prompt_rewrite_text_to_image_forms.md",
        "prompts": "prompts/vcg_prompt_rewrite_text_to_image_instructions.md",
        "inputs": "inputs/vcg_prompt_rewrite_text_to_image_inputs.md",
    },
    "WRITING_TOOL_PROOFREAD_V2": {
        "guidelines": "guidelines/writing_tool_proofread_v2.md",
        "forms": "forms/writing_tool_proofread_v2_forms.md",
        "prompts": "prompts/writing_tool_proofread_v2_instructions.md",
        "inputs": "inputs/writing_tool_proofread_v2_inputs.md",
    },
    "TA_PERSONALIZED_SMART_REPLY": {
        "guidelines": "guidelines/ta_personalized_smart_reply.md",
        "forms": "forms/ta_personalized_smart_reply_forms.md",
        "prompts": "prompts/ta_personalized_smart_reply_instructions.md",
        "inputs": "inputs/ta_personalized_smart_reply_inputs.md",
    },
    "TA_WRITING_TOOLS_WRITING_QA": {
        "guidelines": "guidelines/ta_writing_tools_writing_QA.md",
        "forms": "forms/ta_writing_tools_writing_QA_forms.md",
        "prompts": "prompts/ta_writing_tools_writing_QA_instructions.md",
        "inputs": "inputs/ta_writing_tools_writing_QA_inputs.md",
    },
}

# ══════════════════════════════════════════════════════════════════════════
# LANGUAGE-SPECIFIC BEHAVIORAL ANCHORS
# ══════════════════════════════════════════════════════════════════════════
LANGUAGE_ANCHORS: dict[str, str] = {
    "TH": """\
=== THAI LANGUAGE BEHAVIORAL ANCHOR ===
Ketika mengevaluasi naturalness dalam Bahasa Thailand:
• Periksa partikel akhir kalimat: ครับ (pria formal), ค่ะ/ค่ะ (wanita formal), นะ/นะครับ (softening)
• Register harus konsisten: formal (ราชาศัพท์) vs standar vs kasual — jangan campur tanpa alasan
• Flag: Anglisisme berlebihan ketika padanan Thai tersedia
• CRITICAL: Salah partikel honorifik di konteks formal = otomatis -1 Localization
• Cek: apakah panjang kalimat sesuai natural Thai (cenderung lebih pendek dari Indonesia)
""",
    "JA": """\
=== JAPANESE LANGUAGE BEHAVIORAL ANCHOR ===
Ketika mengevaluasi naturalness dalam Bahasa Jepang:
• KEIGO adalah WAJIB di konteks profesional: Teineigo (丁寧語), Sonkeigo (尊敬語), Kenjōgo (謙譲語)
• Konsistensi desu/masu form vs plain form — jangan flip-flop dalam satu respons
• Kanji level: terlalu banyak kanji = kaku; terlalu banyak hiragana = childish
• Flag: romaji tanpa alasan, mixing script yang tidak perlu
• CRITICAL: Salah KEIGO level = -2 Localization (ini sangat penting bagi penutur asli)
• Cek: apakah onomatopeia/mimesis digunakan secara tepat jika ada
""",
    "KO": """\
=== KOREAN LANGUAGE BEHAVIORAL ANCHOR ===
Ketika mengevaluasi naturalness dalam Bahasa Korea:
• Level bahasa: 합쇼체 (sangat formal) > 해요체 (formal standar) > 해체 (informal) > 반말 (sangat casual)
• Partikel harus tepat: 이/가 (subject), 을/를 (object), 은/는 (topic marker)
• Honorific suffix: -님 (orang), -씨 (nama) — jangan campur tanpa alasan
• Flag: anglisisme saat padanan Korea lebih natural
• Cek: urutan kata SOV harus dipertahankan (bukan calque dari Inggris)
""",
    "EN": """\
=== ENGLISH LANGUAGE BEHAVIORAL ANCHOR ===
Ketika mengevaluasi naturalness dalam Bahasa Inggris:
• Tentukan dialect target (US vs UK) — dan KONSISTEN: colour vs color, etc.
• Naturalness test: apakah terdengar seperti native speaker atau terjemahan langsung?
• Register: formal (no contractions) vs conversational (contractions OK)
• Flag: false friends dari bahasa lain, calques yang tidak idiomatik
• CRITICAL: Awkward phrasing yang jelas hasil terjemahan = -1 Localization minimum
• Cek: subject-verb agreement, artikel (a/an/the) yang benar
""",
    "ID": """\
=== INDONESIAN LANGUAGE BEHAVIORAL ANCHOR ===
Ketika mengevaluasi naturalness dalam Bahasa Indonesia:
• Gunakan KBBI sebagai referensi: kata baku vs tidak baku (contoh: "aktif" bukan "aktip")
• Imbuhan harus tepat: me-/ber-/ter-/pe- sesuai kaidah
• Flag: campur kode Inggris yang tidak perlu ketika kata Indonesia tersedia
• Kalimat pasif berlebihan tidak natural — preferensikan aktif
• CRITICAL: Kesalahan imbuhan yang mengubah makna = -2 Truthfulness
• Cek: apakah gaya formal/informal sesuai konteks (formal = tidak gunakan kata gaul)
""",
    "MS": """\
=== MALAY LANGUAGE BEHAVIORAL ANCHOR ===
Ketika mengevaluasi naturalness dalam Bahasa Malaysia:
• Ejaan Malaysia berbeda dari Indonesia: "telefon" bukan "telepon", "awak" bukan "kamu"
• Penggunaan partikel: "lah", "kan", "mah" — kontekstual, jangan berlebihan di teks formal
• Register: Bahasa Malaysia formal (surat resmi) sangat berbeda dari bahasa pasar
• Flag: pengaruh Indonesia yang berlebihan (ini Malay, bukan Indonesia)
""",
    "VI": """\
=== VIETNAMESE LANGUAGE BEHAVIORAL ANCHOR ===
Ketika mengevaluasi naturalness dalam Bahasa Vietnam:
• Tonal markers (diacritic) harus benar — typo di tanda nada mengubah makna sepenuhnya
• Pronoun sistem sangat kontekstual: tôi/bạn/anh/chị/em — pilih sesuai relasi pembicara
• Perbedaan dialek: Utara (Hà Nội) vs Selatan (TP.HCM) — flag jika tidak konsisten
• CRITICAL: Satu karakter salah tonal = kata berbeda = -1 minimum Localization
""",
    "ZH": """\
=== MANDARIN LANGUAGE BEHAVIORAL ANCHOR ===
Ketika mengevaluasi naturalness dalam Bahasa Mandarin:
• Tentukan target: Simplified (mainland China) vs Traditional (Taiwan/HK) — KONSISTEN
• Measure words (量词) harus tepat: 一本书 bukan 一个书
• Calque dari Inggris yang tidak natural di Mandarin = flag
• Cek: apakah 的/地/得 digunakan dengan benar (sangat sering salah)
""",
    "AR": """\
=== ARABIC LANGUAGE BEHAVIORAL ANCHOR ===
Ketika mengevaluasi naturalness dalam Bahasa Arab:
• Tentukan target: MSA (فصحى) vs dialek regional — jangan campur tanpa konteks
• Gender agreement (mudzakkar/muannats) WAJIB tepat — ini fundamental
• Dual form dan plural tidak beraturan harus benar (jangan hanya tambah ون/ات)
• CRITICAL: Salah gender agreement = -1 Localization otomatis
• Cek: hamza placement, tashkeel jika diperlukan
""",
}

# ══════════════════════════════════════════════════════════════════════════
# DYNAMIC SELF-AUDIT PER TASK
# ══════════════════════════════════════════════════════════════════════════
TASK_SELF_AUDIT: dict[str, str] = {
    "PR": """\
=== PR SELF-AUDIT — LAKUKAN INI SEBELUM OUTPUT ===
□ Apakah skor Satisfaction setiap response (1-5) konsisten dengan semua dimensi?
□ Apakah ranking A/B/C mathemetically derived dari skor Satisfaction?
□ Apakah setiap skor < 3 disertai evidence spesifik dari teks (kutip bagian yang salah)?
□ Apakah ada hallucination faktual yang saya lewatkan?
□ Apakah essay reasoning tersedia dalam bahasa Indonesia DAN bahasa Inggris?
□ PENALTY CHECK: -1/-2 sudah diterapkan sesuai satisfaction logic table di Guidelines?
□ Apakah Localization dinilai dari perspektif penutur asli {lang_name}?
""",
    "AFM": """\
=== AFM SELF-AUDIT — LAKUKAN INI SEBELUM OUTPUT ===
□ Apakah saya membaca GAQ secara berurutan: 1a → 1b → 2a → 3 → 4/5 → 6 → 7?
□ Jika response "engage": apakah GAQ 4, 6a, 6b semua dijawab?
□ Jika response "not engage": apakah GAQ 5a/5b/5c semua dijawab?
□ Apakah Heuristic Satisfaction Score (GAQ 7) konsisten dengan safety assessment?
□ Apakah reasoning essay dalam bahasa Inggris?
□ Apakah alasan pilihan dalam Bahasa Indonesia (1 kalimat)?
□ Apakah semua safety flag sudah diperiksa (tidak ada yang terlewat)?
""",
    "CYU_WEBSITE_TOPIC": """\
=== CYU SELF-AUDIT — LAKUKAN INI SEBELUM OUTPUT ===
□ Apakah topic identification correct dan sesuai boundary case di Guidelines?
□ Apakah Instruction Following konsisten dengan topic identification?
□ Apakah Groundedness check sudah mempertimbangkan fabricated/hallucinated topics?
□ Apakah Satisfaction derived dari semua dimensi di atas secara logis?
□ Apakah pairwise comparison konsisten dengan individual satisfaction scores?
""",
    "CYU_TOPLINE_SUMMARIZATION": """\
=== CYU TOPLINE SELF-AUDIT — LAKUKAN INI SEBELUM OUTPUT ===
□ Apakah main idea dan key points dari original text sudah teridentifikasi dengan benar?
□ Apakah safety check pada input text sudah dilakukan?
□ Apakah Comprehensiveness assessment mencakup semua poin penting?
□ Apakah Groundedness check ketat terhadap hallucination di summary?
□ Apakah Composition check mempertimbangkan boilerplate dan localization?
□ Apakah Satisfaction Categorization konsisten dengan semua dimensi di atas?
""",
    "TC_MESSAGE_REPLY": """\
=== TC MESSAGE REPLY SELF-AUDIT — LAKUKAN INI SEBELUM OUTPUT ===
□ Apakah saya menilai Groundedness dari sudut pandang situasi user yang sebenarnya?
□ Apakah Comprehensiveness mempertimbangkan SEMUA aspek dalam user request?
□ Apakah Composition assessment konsisten dengan Localization check?
□ Apakah Harmlessness diperiksa sebelum memberikan Satisfaction rating?
□ Apakah pairwise comparison logically derived dari skor individual?
""",
    "TC_PROOFREADING": """\
=== TC PROOFREADING SELF-AUDIT — LAKUKAN INI SEBELUM OUTPUT ===
□ Apakah saya membandingkan original text vs proofread output secara line-by-line?
□ Apakah setiap perubahan dinilai: necessary vs unnecessary edit?
□ Apakah register/tone dipertahankan dari original (jangan over-formalize)?
□ Apakah Localization check mempertimbangkan gaya penulisan lokal?
□ Apakah skor Satisfaction konsisten dengan kualitas proofreading secara keseluruhan?
""",
    "VCG_ADM_BASE_CREATION": """\
=== VCG BASE CREATION SELF-AUDIT — LAKUKAN INI SEBELUM OUTPUT ===
□ Apakah safety flags diperiksa PERTAMA sebelum quality assessment?
□ Apakah Visual Quality Issues sudah mencakup: contrast, blur, stretch, rotation?
□ Apakah Text in Image (jika ada) diperiksa akurasi dan alignment-nya?
□ Apakah Structural Integrity mempertimbangkan anatomy, proporsi, dan perspektif?
□ Apakah Input/Output Alignment dinilai secara ketat terhadap prompt asli?
□ Apakah pairwise comparison (A↔B, C↔B, A↔C) semua konsisten satu sama lain?
""",
    "TA_PERSONALIZED_SMART_REPLY": """\
=== PSR SELF-AUDIT — LAKUKAN INI SEBELUM OUTPUT ===
□ Apakah saya membaca full conversation history sebelum menilai?
□ Apakah User Profiles dipertimbangkan dalam Personalization assessment?
□ Apakah Harmfulness Assessment (A1/A2/B1/B2) sudah dijawab semua?
□ Apakah Tone & Empathy Alignment dinilai sesuai konteks emotional conversation?
□ Apakah Personalization score mencerminkan seberapa baik response "fit" user profile?
□ Apakah pairwise A vs B comparison konsisten dengan skor individual?
□ Apakah insights essay dalam bahasa Inggris, dan alasan pilihan dalam Bahasa Indonesia?
""",
    "TA_WRITING_TOOLS_WRITING_QA": """\
=== WRITING QA SELF-AUDIT — LAKUKAN INI SEBELUM OUTPUT ===
□ Apakah User Query sudah dikategorikan dengan benar (Part I)?
□ Apakah semua 4 aspek Accuracy & Relevance dijawab?
□ Apakah Conciseness dinilai relatif terhadap jenis query (bukan absolut)?
□ Apakah Tone & Style sesuai konteks penulisan yang diminta user?
□ Apakah Educational Value relevant untuk jenis query ini?
□ Apakah Localization Issues diperiksa dari perspektif penutur asli {lang_name}?
□ Apakah Grading Summary (Excellent/Good/Fair/Poor) konsisten dengan dimensi di atas?
□ Apakah pairwise comparison di Part III logically derived?
""",
    "WRITING_TOOL_PROOFREAD_V2": """\
=== PROOFREADING V2 SELF-AUDIT — LAKUKAN INI SEBELUM OUTPUT ===
□ Apakah Formality Level original text sudah diidentifikasi dengan benar?
□ Apakah Q1 & Q2 Initial Assessment sudah dijawab?
□ Apakah setiap edit dikategorikan: Necessary vs Unnecessary?
□ Apakah Completeness check mempertimbangkan error yang SEHARUSNYA diperbaiki tapi tidak?
□ Apakah pairwise comparison konsisten dengan Correctness dan Completeness scores?
""",
}

# ══════════════════════════════════════════════════════════════════════════
# OUTPUT CONTRACT TEMPLATE (Universal)
# ══════════════════════════════════════════════════════════════════════════
OUTPUT_CONTRACT = """\
================================================================================
BLOCK D — OUTPUT CONTRACT (WAJIB DIIKUTI 100% — TIDAK BOLEH DILEWATI)
================================================================================

Struktur output kamu HARUS mengikuti template berikut PERSIS.
Jangan menambahkan section baru. Jangan menghilangkan section yang ada.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 PRE-EVALUATION AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• User Intent  : [1 kalimat — apa yang user minta dari AI]
• Task Type    : {task_display_name}
• Target Lang  : {lang_name} ({iso_code})
• Red Flags    : [flag masalah sebelum evaluasi dimulai, atau "None detected"]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 EVALUATION RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Isi form evaluasi sesuai BLOCK C (Forms) di atas — setiap pertanyaan WAJIB dijawab]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚖️ SELF-AUDIT RESULT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Score Consistency  : [✅ Konsisten / ❌ Tidak — jelaskan jika tidak]
• Penalties Applied  : [List -1/-2 yang diberikan, atau "None"]
• Hallucination Flag : [✅ Ditemukan: "..." / ❌ Tidak ditemukan]
• {lang_name} Naturalness: [✅ Pass / ❌ Fail — bukti spesifik jika Fail]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 ANNOTATOR RECOMMENDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1-2 kalimat: apa yang perlu diperhatikan annotator sebelum submit hasil ini]
================================================================================
"""

# ══════════════════════════════════════════════════════════════════════════
# MASTER TEMPLATE V2 (Optimized Block Order)
# ══════════════════════════════════════════════════════════════════════════
MASTER_TEMPLATE_V2 = """\
================================================================================
MASTER SYSTEM PROMPT — CENTIFIC ANNOTATION EVALUATOR [v2.0 OPTIMIZED]
================================================================================
ROLE          : Skeptical Senior Annotator — 5+ Years AI Evaluation Experience
TARGET LANG   : {lang_name} ({iso_code})
TASK TYPE     : {task_display_name}
================================================================================

████████████████████████████████████████████████████████████████████████████████
BLOCK A — IDENTITY & BEHAVIORAL CONTRACT
(BACA INI PERTAMA — WAJIB DIPATUHI 100% SEPANJANG EVALUASI)
████████████████████████████████████████████████████████████████████████████████

Kamu adalah SKEPTICAL SENIOR ANNOTATOR dengan 5+ tahun pengalaman evaluasi AI
di platform Centific. Kamu tidak menilai "kesan pertama" — kamu menggali deep.

KARAKTER KAMU:
• AUDITOR DINGIN: Tidak terpengaruh panjang/kefasihan respons. Fokus pada
  AKURASI, RELEVANSI, dan KUALITAS NYATA.
• NATIVE SPEAKER SIMULATOR: Mengevaluasi naturalness dari sudut pandang penutur
  asli {lang_name}. Salah satu kesalahan linguistik sudah cukup untuk penalty.
• SCORE ENGINEER: Setiap skor HARUS mathematically consistent. Tidak ada skor
  "mengambang" tanpa justifikasi berbasis evidence.
• HALLUCINATION HUNTER: Setiap klaim faktual yang tidak bisa diverifikasi dari
  konteks input = SUSPECT. Flag dan beri penalty.

BEHAVIORAL RULES — TIDAK BOLEH DILANGGAR:
1. JANGAN menilai berdasarkan panjang respons saja.
2. Setiap skor < 3 (dari 5) WAJIB disertai evidence spesifik (kutip bagian yang
   salah dari respons yang dievaluasi).
3. Format output HARUS mengikuti OUTPUT CONTRACT di Block D — tidak boleh ada
   section yang dilewati atau diubah strukturnya.
4. Bahasa reasoning: Bahasa Indonesia untuk ringkasan/alasan pilihan,
   Bahasa Inggris untuk evaluasi teknis — KECUALI task menentukan sebaliknya.
5. Jangan balik bertanya ke user. Evaluasi langsung berdasarkan input yang ada.
6. Ranking harus DERIVED dari skor Satisfaction — bukan opini intuitif.

{self_audit}

████████████████████████████████████████████████████████████████████████████████
BLOCK B — PROJECT GUIDELINES (THE BRAIN)
(Ini adalah sumber kebenaran — rujuk ini untuk SEMUA keputusan penilaian)
████████████████████████████████████████████████████████████████████████████████

{guidelines_content}

████████████████████████████████████████████████████████████████████████████████
BLOCK C — LANGUAGE-SPECIFIC BEHAVIORAL ANCHOR
(Panduan spesifik untuk evaluasi naturalness dalam {lang_name})
████████████████████████████████████████████████████████████████████████████████

{language_anchor}

████████████████████████████████████████████████████████████████████████████████
BLOCK D — TASK EXECUTION INSTRUCTIONS & OUTPUT TEMPLATE
(Panduan teknis cara mengerjakan task, format input, dan template output wajib)
████████████████████████████████████████████████████████████████████████████████

{prompts_content}

================================================================================
END OF MASTER SYSTEM PROMPT v2.0 — CENTIFIC ANNOTATION EVALUATOR
Task: {task_display_name} | Language: {lang_name} ({iso_code})
================================================================================
"""


# ══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════

def read_asset_file(filepath: str) -> str:
    """Membaca isi file asset. Raises FileNotFoundError jika tidak ditemukan."""
    abs_path = os.path.abspath(filepath)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"Asset file tidak ditemukan: {abs_path}")
    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()
    logger.info(f"Loaded asset: {abs_path} ({len(content)} chars)")
    return content


def _get_task_display_name(task_code: str) -> str:
    """Konversi task_code ke display name yang human-readable."""
    TASK_DISPLAY = {
        "PR": "PR Fine Tuning — Preference Ranking",
        "AFM": "AFM — Safety Guide (Multi Modal)",
        "TC_MESSAGE_REPLY": "Text Composition — TC Message Reply",
        "TC_PROOFREADING": "Text Composition — TC Proofreading",
        "CYU_WEBSITE_TOPIC": "CYU — Website Topic Identification",
        "CYU_TOPLINE_SUMMARIZATION": "CYU — Topline Summarization",
        "VCG_ADM_BASE_CREATION": "VCG — ADM Base Creation Model",
        "VCG_BACKGROUND_MESSAGE": "VCG — Background Message",
        "VCG_EDIT_MODEL": "VCG — Edit Model",
        "VCG_PROMPT_REWRITE": "VCG — Prompt Rewrite Variety Review",
        "WRITING_TOOL_PROOFREAD_V2": "Writing Tool — Proofreading V2",
        "TA_PERSONALIZED_SMART_REPLY": "TA/TC — Personalized Smart Reply",
        "TA_WRITING_TOOLS_WRITING_QA": "TA/TC — Writing QA",
    }
    return TASK_DISPLAY.get(task_code.upper(), task_code.replace("_", " "))


# ══════════════════════════════════════════════════════════════════════════
# MAIN ASSEMBLY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════

def assemble_evaluator_prompt(lang_code: str, task_code: str = "PR") -> str:
    """
    OPTIMIZED v2.0 — Main entry point (backward compatible dengan v1).

    Merakit evaluator prompt dengan:
    1. Urutan block optimal: Role → Brain → Interface → Contract → Execute → Edge Cases → Language
    2. Dynamic Language Anchor per bahasa
    3. Dynamic Self-Audit per task_code
    4. Output Contract yang eksplisit dan terstruktur

    Args:
        lang_code: Kode bahasa (TH, JA, EN, ID, KO, MS, VI, ZH, AR)
        task_code: Kode task (PR, AFM, TC_MESSAGE_REPLY, dst.)

    Returns:
        String prompt lengkap siap dikirim ke LLM sebagai system prompt.
    """
    lang_name, iso_code = LANGUAGE_MAP.get(
        lang_code.upper(), ("Bahasa Inggris", "en")
    )
    task_code_upper = task_code.upper()
    config = ASSET_CONFIGS.get(task_code_upper, ASSET_CONFIGS["PR"])
    task_display = _get_task_display_name(task_code_upper)

    # Load assets
    try:
        guidelines_content = read_asset_file(os.path.join(ASSETS_DIR, config["guidelines"]))
        prompts_content = read_asset_file(os.path.join(ASSETS_DIR, config["prompts"]))
    except FileNotFoundError as e:
        logger.error(f"Asset load error: {e}")
        raise

    # Dynamic components
    language_anchor = LANGUAGE_ANCHORS.get(lang_code.upper(), "")
    self_audit_raw = TASK_SELF_AUDIT.get(task_code_upper, "")
    self_audit = self_audit_raw.replace("{lang_name}", lang_name)

    # Output contract with task-specific injection
    output_contract = OUTPUT_CONTRACT.format(
        task_display_name=task_display,
        lang_name=lang_name,
        iso_code=iso_code,
    )

    # Assemble full prompt
    prompt = MASTER_TEMPLATE_V2.format(
        lang_name=lang_name,
        iso_code=iso_code,
        task_display_name=task_display,
        guidelines_content=guidelines_content,
        prompts_content=prompts_content,
        language_anchor=language_anchor,
        self_audit=self_audit,
    )

    logger.info(
        f"[v2.0] Evaluator prompt assembled: lang={lang_name} ({iso_code}), "
        f"task={task_code_upper}, total={len(prompt)} chars"
    )
    return prompt


# Alias untuk backward compatibility (kalau ada kode lama yang pakai ini)
def assemble_master_prompt(lang_code: str, task_code: str = "PR") -> str:
    """Alias backward-compatible ke assemble_evaluator_prompt."""
    return assemble_evaluator_prompt(lang_code, task_code)


def assemble_evaluator_prompt_v1_legacy(lang_code: str, task_code: str = "PR") -> str:
    """
    Legacy v1 prompt assembler — simpan untuk A/B testing.
    Gunakan ini jika ingin membandingkan hasil v1 vs v2.
    """
    lang_name, iso_code = LANGUAGE_MAP.get(lang_code.upper(), ("Bahasa Inggris", "en"))
    config = ASSET_CONFIGS.get(task_code.upper(), ASSET_CONFIGS["PR"])

    guidelines_content = read_asset_file(os.path.join(ASSETS_DIR, config["guidelines"]))
    forms_content = read_asset_file(os.path.join(ASSETS_DIR, config["forms"]))
    prompts_content = read_asset_file(os.path.join(ASSETS_DIR, config["prompts"]))
    inputs_content = read_asset_file(os.path.join(ASSETS_DIR, config["inputs"]))

    # v1 Critical Thinking Preamble (original)
    ct_preamble = f"""\
=== SYSTEM INSTRUCTION: CRITICAL THINKING PROTOCOL ===
You are a SKEPTICAL SENIOR ANNOTATOR with 5+ years of experience in AI evaluation.
Your mindset is that of a cynical, data-driven auditor — you NEVER take AI responses at face value.

CORE DIRECTIVES:
1. HUNT for subtle hallucinations, logical fallacies, and unsupported claims.
2. CROSS-REFERENCE every factual claim against the provided Guidelines.
3. CHALLENGE the surface-level reading: does the response TRULY serve the user's intent,
   or does it merely appear to follow instructions?
4. APPLY the -1/-2 penalty protocol STRICTLY per the Satisfaction Logic table.
5. VERIFY linguistic naturalness from the perspective of a NATIVE speaker of {lang_name}.
6. Your ranking MUST be mathematically consistent with your dimension scores.

SELF-AUDIT CHECKLIST (perform silently before outputting):
- Did I miss any subtle hallucinations or fabricated references?
- Is my satisfaction rating consistent with my dimension penalties?
- Is my preference ranking logically derived from my satisfaction ratings?
- Have I applied the native linguistic rules of {lang_name} correctly?
=== END CRITICAL THINKING PROTOCOL ===
"""

    master = f"""\
================================================================================
MASTER SYSTEM PROMPT — CENTIFIC PREFERENCE RANKING EVALUATOR [v1 LEGACY]
================================================================================
TARGET LANGUAGE      : {lang_name}
TARGET LANGUAGE CODE : {iso_code}
================================================================================

SECTION 1: WORKFLOW & PROMPT INSTRUCTIONS
================================================================================
{prompts_content}

================================================================================
SECTION 2: PROJECT GUIDELINES (THE BRAIN)
================================================================================
{guidelines_content}

================================================================================
SECTION 3: EVALUATION FORM (THE INTERFACE)
================================================================================
{forms_content}

================================================================================
SECTION 4: INPUT HANDLING RULES
================================================================================
{inputs_content}

================================================================================
END OF MASTER SYSTEM PROMPT [v1 LEGACY]
================================================================================
"""

    return f"{ct_preamble}\n\n{master}"

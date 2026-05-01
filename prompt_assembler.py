"""
prompt_assembler.py
-------------------
Modul untuk membaca asset file (guidelines, forms, prompts, inputs)
dan merakit MASTER_SYSTEM_PROMPT yang siap dikirim ke LLM.

Termasuk `assemble_evaluator_prompt()` dengan injeksi
persona "Skeptical Senior Annotator" + Critical Thinking.
"""

import os
import logging

logger = logging.getLogger(__name__)

# ── Direktori root assets (relatif terhadap lokasi file ini) ──────────────
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
# Task code bisa utama (PR, CYU) atau subtask (TC_MESSAGE_REPLY, TC_PROOFREADING)
ASSET_CONFIGS = {
    "PR": {
        "guidelines": "guidelines/pr_preference_ranking.md",
        "forms":      "forms/pr_forms.md",
        "prompts":    "prompts/pr_prompt_instructions.md",
        "prompts_pro": "prompts/pr_prompt_instructions_pro.md",
        "inputs":     "inputs/pr_inputs.md",
    },
    "AFM": {
        "guidelines": "guidelines/afm_safety_guide.md",
        "forms":      "forms/afm_safety_guide_forms.md",
        "prompts":    "prompts/afm_safety_guide_instructions.md",
        "inputs":     "inputs/afm_safety_guide_inputs.md",
    },
    "TC_MESSAGE_REPLY": {
        "guidelines": "guidelines/tc_message_reply.md",
        "forms":      "forms/tc_message_reply_forms.md",
        "prompts":    "prompts/tc_message_reply_instructions.md",
        "inputs":     "inputs/tc_message_reply_inputs.md",
    },
    "TC_PROOFREADING": {
        "guidelines": "guidelines/tc_proofreading.md",
        "forms":      "forms/tc_proofreading_forms.md",
        "prompts":    "prompts/tc_proofreading_instructions.md",
        "inputs":     "inputs/tc_proofreading_inputs.md",
    },
    "CYU": {
        "guidelines": "guidelines/cyu_website_topic.md",
        "forms":      "forms/cyu_website_topic_forms.md",
        "prompts":    "prompts/cyu_website_topic_instructions.md",
        "inputs":     "inputs/cyu_website_topic_inputs.md",
    },
    "CYU_TOPLINE_SUMMARIZATION": {
        "guidelines": "guidelines/cyu_topline_summarization.md",
        "forms":      "forms/cyu_topline_summarization_forms.md",
        "prompts":    "prompts/cyu_topline_summarization_instructions.md",
        "inputs":     "inputs/cyu_topline_summarization_inputs.md",
    },
    "CYU_WEBSITE_TOPIC": {
        "guidelines": "guidelines/cyu_website_topic.md",
        "forms":      "forms/cyu_website_topic_forms.md",
        "prompts":    "prompts/cyu_website_topic_instructions.md",
        "inputs":     "inputs/cyu_website_topic_inputs.md",
    },
    # VCG — Visual Content Generation
    # ADM Creation & Base Creation Model share the same asset set
    "VCG_ADM_BASE_CREATION": {
        "guidelines": "guidelines/vcg_adm_creation_or_base_creation_model.md",
        "forms":      "forms/vcg_adm_or_base_creation_model_forms.md",
        "prompts":    "prompts/vcg_adm_or_base_creation_model_instructions.md",
        "inputs":     "inputs/vcg_adm_or_base_creation_model_inputs.md",
    },
    "VCG_BACKGROUND_MESSAGE": {
        "guidelines": "guidelines/vcg_background_message.md",
        "forms":      "forms/vcg_background_message_forms.md",
        "prompts":    "prompts/vcg_background_message_instructions.md",
        "inputs":     "inputs/vcg_background_message_inputs.md",
    },
    "VCG_EDIT_MODEL": {
        "guidelines": "guidelines/vcg_edit_model.md",
        "forms":      "forms/vcg_edit_model_forms.md",
        "prompts":    "prompts/vcg_edit_model_instructions.md",
        "inputs":     "inputs/vcg_edit_model_inputs.md",
    },
    "VCG_PROMPT_REWRITE": {
        "guidelines": "guidelines/vcg_prompt_rewrite_text_to_image.md",
        "forms":      "forms/vcg_prompt_rewrite_text_to_image_forms.md",
        "prompts":    "prompts/vcg_prompt_rewrite_text_to_image_instructions.md",
        "inputs":     "inputs/vcg_prompt_rewrite_text_to_image_inputs.md",
    },
    "WRITING_TOOL_PROOFREAD_V2": {
        "guidelines": "guidelines/writing_tool_proofread_v2.md",
        "forms":      "forms/writing_tool_proofread_v2_forms.md",
        "prompts":    "prompts/writing_tool_proofread_v2_instructions.md",
        "inputs":     "inputs/writing_tool_proofread_v2_inputs.md",
    },
    "TA_PERSONALIZED_SMART_REPLY": {
        "guidelines": "guidelines/ta_personalized_smart_reply.md",
        "forms":      "forms/ta_personalized_smart_reply_forms.md",
        "prompts":    "prompts/ta_personalized_smart_reply_instructions.md",
        "inputs":     "inputs/ta_personalized_smart_reply_inputs.md",
    },
    "TA_WRITING_TOOLS_WRITING_QA": {
        "guidelines": "guidelines/ta_writing_tools_writing_QA.md",
        "forms":      "forms/ta_writing_tools_writing_QA_forms.md",
        "prompts":    "prompts/ta_writing_tools_writing_QA_instructions.md",
        "inputs":     "inputs/ta_writing_tools_writing_QA_inputs.md",
    },
}

# ── Critical Thinking System Instruction (English) ───────────────────────
CRITICAL_THINKING_PREAMBLE = """\
=== SYSTEM INSTRUCTION: CRITICAL THINKING PROTOCOL ===

You are a SKEPTICAL SENIOR ANNOTATOR with 5+ years of experience in AI evaluation.
Your mindset is that of a cynical, data-driven auditor — you NEVER take AI responses at face value.

CORE DIRECTIVES:
1. HUNT for subtle hallucinations, logical fallacies, and unsupported claims.
2. CROSS-REFERENCE every factual claim against the provided Guidelines.
3. CHALLENGE the surface-level reading: does the response TRULY serve the user's intent,
   or does it merely appear to follow instructions?
4. APPLY the -1/-2 penalty protocol STRICTLY per the Satisfaction Logic table.
5. VERIFY linguistic naturalness from the perspective of a NATIVE speaker of the target language.
6. Your ranking MUST be mathematically consistent with your dimension scores.

SELF-AUDIT CHECKLIST (perform silently before outputting):
- Did I miss any subtle hallucinations or fabricated references?
- Is my satisfaction rating consistent with my dimension penalties?
- Is my preference ranking logically derived from my satisfaction ratings?
- Have I applied the native linguistic rules of {{TARGET_LANGUAGE}} correctly?

=== END CRITICAL THINKING PROTOCOL ===
"""


def read_asset_file(filepath: str) -> str:
    """
    Membaca isi file dari filesystem.
    Raises FileNotFoundError jika file tidak ditemukan.
    """
    abs_path = os.path.abspath(filepath)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"Asset file tidak ditemukan: {abs_path}")

    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()

    logger.info(f"Loaded asset: {abs_path} ({len(content)} chars)")
    return content


def assemble_master_prompt(lang_code: str, task_code: str = "PR", tier: str = "BASIC") -> str:
    """
    Merakit MASTER_SYSTEM_PROMPT dasar dari semua asset file berdasarkan task_code dan tier.
    """
    lang_name, iso_code = LANGUAGE_MAP.get(
        lang_code.upper(), ("Bahasa Inggris", "en")
    )

    config = ASSET_CONFIGS.get(task_code.upper(), ASSET_CONFIGS["PR"])
    
    guidelines_content = read_asset_file(os.path.join(ASSETS_DIR, config["guidelines"]))
    forms_content      = read_asset_file(os.path.join(ASSETS_DIR, config["forms"]))
    
    if tier.upper() in ["PRO", "PREMIUM"] and "prompts_pro" in config:
        prompts_path = config["prompts_pro"]
    else:
        prompts_path = config["prompts"]
        
    prompts_content    = read_asset_file(os.path.join(ASSETS_DIR, prompts_path))
    inputs_content     = read_asset_file(os.path.join(ASSETS_DIR, config["inputs"]))

    master_prompt = f"""\
================================================================================
MASTER SYSTEM PROMPT — CENTIFIC PREFERENCE RANKING EVALUATOR
================================================================================

TARGET LANGUAGE     : {lang_name}
TARGET LANGUAGE CODE: {iso_code}

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
END OF MASTER SYSTEM PROMPT
================================================================================
"""

    master_prompt = master_prompt.replace("{{TARGET_LANGUAGE}}", lang_name)
    master_prompt = master_prompt.replace("{{TARGET_LANGUAGE_CODE}}", iso_code)

    logger.info(
        f"Master prompt assembled: lang={lang_name} ({iso_code}), "
        f"total {len(master_prompt)} chars"
    )
    return master_prompt


def assemble_evaluator_prompt(lang_code: str, task_code: str = "PR", tier: str = "BASIC") -> str:
    """
    Merakit EVALUATOR PROMPT lengkap dengan:
    1. Critical Thinking preamble (Skeptical Senior Annotator persona)
    2. Master system prompt (guidelines + forms + prompts + inputs)
    3. TARGET_LANGUAGE injection

    Ini adalah fungsi utama yang dipanggil oleh bot sebelum hit ke LLM.
    """
    lang_name, iso_code = LANGUAGE_MAP.get(
        lang_code.upper(), ("Bahasa Inggris", "en")
    )

    # 1. Inject language into Critical Thinking preamble
    ct_prompt = CRITICAL_THINKING_PREAMBLE.replace("{{TARGET_LANGUAGE}}", lang_name)

    # 2. Rakit master prompt
    master = assemble_master_prompt(lang_code, task_code, tier)

    # 3. Gabungkan
    evaluator_prompt = f"{ct_prompt}\n\n{master}"

    logger.info(
        f"Evaluator prompt assembled: lang={lang_name}, "
        f"total {len(evaluator_prompt)} chars (CT preamble + master)"
    )
    return evaluator_prompt

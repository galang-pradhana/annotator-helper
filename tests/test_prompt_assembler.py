import pytest
from unittest.mock import patch, mock_open
from prompt_assembler import assemble_evaluator_prompt, LANGUAGE_MAP, ASSET_CONFIGS

def test_language_map():
    assert "ID" in LANGUAGE_MAP
    assert LANGUAGE_MAP["ID"] == ("Bahasa Indonesia", "id")

@patch("prompt_assembler.read_asset_file")
def test_assemble_evaluator_prompt_basic(mock_read):
    # Setup mock content for each asset file
    mock_read.return_value = "Mock Content"
    
    # Execute
    prompt = assemble_evaluator_prompt("ID", "PR")
    
    # Assert
    assert "SKEPTICAL SENIOR ANNOTATOR" in prompt
    assert "Bahasa Indonesia" in prompt
    assert "id" in prompt
    assert "Mock Content" in prompt
    # Ensure it called read_asset_file for each asset (guidelines, forms, prompts, inputs)
    assert mock_read.call_count == 4

@patch("prompt_assembler.read_asset_file")
def test_assemble_evaluator_prompt_fallback_lang(mock_read):
    mock_read.return_value = "Mock Content"
    
    # Execute with non-existent lang code
    prompt = assemble_evaluator_prompt("XX", "PR")
    
    # Assert (Should fallback to English)
    assert "Bahasa Inggris" in prompt
    assert "en" in prompt

@patch("prompt_assembler.read_asset_file")
def test_assemble_evaluator_prompt_different_task(mock_read):
    mock_read.return_value = "Mock Content"
    
    # Execute with TC_MESSAGE_REPLY task
    prompt = assemble_evaluator_prompt("ID", "TC_MESSAGE_REPLY")
    
    # Assert
    assert "Bahasa Indonesia" in prompt
    assert mock_read.call_count == 4

def test_asset_configs_structure():
    # Verify that all configs have the required keys
    required_keys = {"guidelines", "forms", "prompts", "inputs"}
    for task_code, config in ASSET_CONFIGS.items():
        assert required_keys.issubset(config.keys()), f"Task {task_code} is missing keys"

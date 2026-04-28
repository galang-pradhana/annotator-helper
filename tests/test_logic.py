import pytest
from bot import _split_message, _calculate_dynamic_price, _extract_database_content, is_balance_sufficient

def test_split_message_basic():
    text = "Hello\nWorld"
    chunks = _split_message(text, 5)
    assert chunks == ["Hello", "World"]

def test_split_message_no_newline():
    text = "ABCDEFGHIJ"
    chunks = _split_message(text, 3)
    assert chunks == ["ABC", "DEF", "GHI", "J"]

def test_calculate_dynamic_price_basic():
    price = _calculate_dynamic_price("BASIC", 500)
    assert 80 <= price <= 90
    
    price_long = _calculate_dynamic_price("BASIC", 5000)
    assert 105 <= price_long <= 120

def test_calculate_dynamic_price_pro():
    price = _calculate_dynamic_price("PRO", 500)
    assert 200 <= price <= 220

def test_extract_database_content_with_tags():
    text = "Some text <database>Important Data</database> other text"
    result = _extract_database_content(text)
    assert result == "Important Data"

def test_extract_database_content_no_tags():
    text = "Just plain text"
    result = _extract_database_content(text)
    assert result == "Just plain text"

def test_extract_database_content_case_insensitive():
    text = "<DATABASE>Mixed Case</DATABASE>"
    result = _extract_database_content(text)
    assert result == "Mixed Case"

def test_is_balance_sufficient():
    assert is_balance_sufficient(100, 50) is True
    assert is_balance_sufficient(50, 100) is False
    assert is_balance_sufficient(50, 50) is True

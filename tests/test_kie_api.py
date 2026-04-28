import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from kie_api import call_kie_ai_api, _is_maintenance_error

def test_is_maintenance_error():
    assert _is_maintenance_error("Server is being maintained") is True
    assert _is_maintenance_error("Under maintenance") is True
    assert _is_maintenance_error("Normal error") is False
    assert _is_maintenance_error(None) is False

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_call_kie_ai_api_success(mock_post):
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test Reply"}}],
        "credits_consumed": 5
    }
    mock_post.return_value = mock_response
    
    # Execute
    # Set env vars to avoid dummy mode
    with patch.dict("os.environ", {"KIE_API_URL": "http://api.test", "KIE_API_KEY": "test-key"}):
        reply = await call_kie_ai_api("system", "user")
    
    # Assert
    assert reply == "Test Reply"
    mock_post.assert_called_once()

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_call_kie_ai_api_http_error_no_retry(mock_post):
    # Setup: 401 Unauthorized (Client Error)
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_post.return_value = mock_response
    
    # Execute
    with patch.dict("os.environ", {"KIE_API_URL": "http://api.test", "KIE_API_KEY": "wrong-key"}):
        reply = await call_kie_ai_api("system", "user")
    
    # Assert
    assert "Client Error 401" in reply
    # Should not retry for 4xx
    assert mock_post.call_count == 1

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
@patch("asyncio.sleep", return_value=None) # Speed up test
async def test_call_kie_ai_api_server_error_retry(mock_sleep, mock_post):
    # Setup: 500 Server Error
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_post.return_value = mock_response
    
    # Execute
    with patch.dict("os.environ", {"KIE_API_URL": "http://api.test", "KIE_API_KEY": "test-key"}):
        reply = await call_kie_ai_api("system", "user")
    
    # Assert
    assert "Server Error 500" in reply
    # Should retry up to MAX_RETRIES (2)
    assert mock_post.call_count == 2

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_call_kie_ai_api_claude_format(mock_post):
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [{"type": "text", "text": "Claude Reply"}]
    }
    mock_post.return_value = mock_response
    
    # Execute
    with patch.dict("os.environ", {"KIE_API_URL": "http://api.test", "KIE_API_KEY": "test-key"}):
        reply = await call_kie_ai_api("system", "user", model_override="claude-3")
    
    # Assert
    assert reply == "Claude Reply"
    # Check payload structure for Claude
    args, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert "system" in payload
    assert payload["system"] == "system"

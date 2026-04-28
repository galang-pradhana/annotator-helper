import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bot import start_command, SELECTING_LANG

@pytest.mark.asyncio
@patch("bot.get_session")
@patch("bot.user_service")
async def test_start_command(mock_user_service, mock_get_session, mock_update, mock_context):
    # Setup
    mock_update.message.reply_text = AsyncMock()
    mock_session = AsyncMock()
    # Mock async context manager
    mock_get_session.return_value.__aenter__.return_value = mock_session
    
    # Mock user_service call
    mock_db_user = MagicMock()
    mock_db_user.balance = 1000
    mock_user_service.register_or_get_user = AsyncMock(return_value=(mock_db_user, True))
    
    # Execute
    result = await start_command(mock_update, mock_context)
    
    # Assert
    assert result == SELECTING_LANG
    mock_update.message.reply_text.assert_called()
    
@pytest.mark.asyncio
@patch("bot.get_session")
@patch("bot.user_service")
async def test_start_command_with_user_data(mock_user_service, mock_get_session, mock_update, mock_context):
    # Setup
    mock_context.user_data["temp"] = "data"
    mock_session = AsyncMock()
    mock_get_session.return_value.__aenter__.return_value = mock_session
    
    mock_db_user = MagicMock()
    mock_db_user.balance = 1000
    mock_user_service.register_or_get_user = AsyncMock(return_value=(mock_db_user, False))
    
    # Execute
    await start_command(mock_update, mock_context)
    
    # Assert
    assert mock_context.user_data == {} # Should be cleared

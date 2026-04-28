import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

@pytest.fixture
def mock_update():
    """Fixture to create a mock Telegram Update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123456789
    update.effective_user.first_name = "TestUser"
    
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = 987654321
    
    update.message = AsyncMock(spec=Message)
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.message = update.message
    
    return update

@pytest.fixture
def mock_context():
    """Fixture to create a mock Telegram Context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot_data = {}
    return context

@pytest.fixture
def mock_session():
    """Fixture for a mock Database Session."""
    session = AsyncMock()
    # add, refresh, and rollback are usually not awaited in some patterns, 
    # but in SQLModel/SQLAlchemy async they are often AsyncMocks.
    # Actually, commit and refresh are awaited. add is not.
    session.add = MagicMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    return session

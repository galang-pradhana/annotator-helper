import pytest
from unittest.mock import AsyncMock, MagicMock
from user_service import register_or_get_user, check_balance, deduct_balance, SIGNUP_BONUS
from models import User

@pytest.mark.asyncio
async def test_register_new_user(mock_session):
    # Setup
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    # Execute
    user, is_new = await register_or_get_user(mock_session, 12345, "newuser")
    
    # Assert
    assert is_new is True
    assert user.user_id == 12345
    assert user.balance == SIGNUP_BONUS
    assert mock_session.add.call_count == 2
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_existing_user(mock_session):
    # Setup
    existing_user = User(user_id=12345, username="olduser", balance=1000)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_user
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    # Execute
    user, is_new = await register_or_get_user(mock_session, 12345, "olduser")
    
    # Assert
    assert is_new is False
    assert user.user_id == 12345
    assert user.balance == 1000
    mock_session.commit.assert_not_called()

@pytest.mark.asyncio
async def test_check_balance(mock_session):
    # Setup
    existing_user = User(user_id=12345, balance=100)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_user
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    # Execute & Assert
    assert await check_balance(mock_session, 12345, 50) is True
    assert await check_balance(mock_session, 12345, 150) is False

@pytest.mark.asyncio
async def test_deduct_balance_success(mock_session):
    # Setup
    existing_user = User(user_id=12345, balance=100)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_user
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    # Execute
    new_balance = await deduct_balance(mock_session, 12345, 40, "PR", "model-x")
    
    # Assert
    assert new_balance == 60
    assert existing_user.balance == 60
    assert mock_session.add.call_count == 2
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_deduct_balance_insufficient(mock_session):
    # Setup
    existing_user = User(user_id=12345, balance=30)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_user
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    # Execute & Assert
    with pytest.raises(ValueError, match="Saldo tidak cukup"):
        await deduct_balance(mock_session, 12345, 40, "PR", "model-x")
    
    mock_session.commit.assert_not_called()

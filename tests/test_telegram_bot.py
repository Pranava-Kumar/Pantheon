"""
Tests for Telegram notification bot.
"""

import pytest
from unittest.mock import patch, MagicMock

from pantheon.notifications.telegram_bot import TelegramSignalBot


class TestTelegramSignalBot:
    """Test Telegram bot functionality."""
    
    @pytest.fixture
    def bot(self):
        """Create bot with mock credentials."""
        return TelegramSignalBot(
            bot_token="test_token",
            chat_id="test_chat_id"
        )
    
    @pytest.fixture
    def sample_signal(self):
        """Sample MMCI signal for testing."""
        return {
            'symbol': 'RELIANCE',
            'direction': 'BUY',
            'consensus_score': 0.65,
            'risk_level': 3,
            'reasoning': 'Strong Q3 earnings, positive sector trend, bullish technical setup',
            'sector': 'Energy',
        }
    
    def test_bot_initialization_enabled(self):
        """Test bot initializes as enabled with credentials."""
        bot = TelegramSignalBot(
            bot_token="test_token",
            chat_id="test_chat_id"
        )
        
        assert bot.enabled is True
        assert bot.bot_token == "test_token"
        assert bot.chat_id == "test_chat_id"
    
    def test_bot_initialization_disabled(self):
        """Test bot initializes as disabled without credentials."""
        bot = TelegramSignalBot()
        
        # Should be disabled if no credentials provided
        assert bot.enabled is False
    
    def test_format_signal_message_buy(self, bot, sample_signal):
        """Test message formatting for BUY signal."""
        message = bot._format_signal_message(sample_signal)
        
        # Check key elements
        assert '🟢' in message  # BUY emoji
        assert 'RELIANCE' in message
        assert 'BUY' in message
        assert '0.650' in message  # Score
        assert '⭐⭐⭐' in message  # Risk level 3
        assert 'Energy' in message
    
    def test_format_signal_message_sell(self, bot, sample_signal):
        """Test message formatting for SELL signal."""
        sample_signal['direction'] = 'SELL'
        message = bot._format_signal_message(sample_signal)
        
        assert '🔴' in message  # SELL emoji
        assert 'SELL' in message
    
    def test_format_signal_message_hold(self, bot, sample_signal):
        """Test message formatting for HOLD signal."""
        sample_signal['direction'] = 'HOLD'
        message = bot._format_signal_message(sample_signal)
        
        assert '🟡' in message  # HOLD emoji
        assert 'HOLD' in message
    
    def test_format_signal_truncates_long_reasoning(self, bot, sample_signal):
        """Test that long reasoning is truncated."""
        sample_signal['reasoning'] = 'A' * 500  # Very long reasoning
        message = bot._format_signal_message(sample_signal)
        
        # Message should be reasonable length (truncated)
        assert len(message) < 600
    
    def test_send_signal_disabled_bot(self, sample_signal):
        """Test sending with disabled bot."""
        bot = TelegramSignalBot()  # No credentials
        
        import asyncio
        result = asyncio.run(bot.send_signal(sample_signal))
        
        assert result is False
    
    def test_send_portfolio_disabled_bot(self):
        """Test portfolio update with disabled bot."""
        bot = TelegramSignalBot()
        
        portfolio = {
            'total_value': 150000,
            'total_pnl': 25000,
            'total_pnl_pct': 20.0,
            'positions': 5,
        }
        
        import asyncio
        result = asyncio.run(bot.send_portfolio_update(portfolio))
        
        assert result is False
    
    def test_send_alert_disabled_bot(self):
        """Test alert with disabled bot."""
        bot = TelegramSignalBot()
        
        import asyncio
        result = asyncio.run(bot.send_alert("Test Alert", "Test message"))
        
        assert result is False
    
    def test_test_connection_disabled_bot(self):
        """Test connection test with disabled bot."""
        bot = TelegramSignalBot()
        
        import asyncio
        result = asyncio.run(bot.test_connection())
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Telegram Bot for Signal Notifications

Sends MMCI signal alerts to Telegram channel/group.
Free to use with Telegram Bot API.

Setup:
1. Create bot via @BotFather on Telegram
2. Get bot token
3. Add bot to your channel/group
4. Get chat_id (forward message to @userinfobot)
5. Add to .env:
   TELEGRAM_BOT_TOKEN=your_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
"""

import asyncio
import aiohttp
from typing import Optional, Dict
from loguru import logger

from pantheon.config.settings import settings


class TelegramSignalBot:
    """
    Telegram bot for sending MMCI signal notifications.
    
    Features:
    - Send BUY/SELL/HOLD signals
    - Include score, risk level, reasoning
    - Format messages for readability
    - Error handling with fallback logging
    """
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize Telegram bot.
        
        Args:
            bot_token: Telegram bot token from @BotFather
            chat_id: Channel/group ID to send messages to
        """
        self.bot_token = bot_token or getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.chat_id = chat_id or getattr(settings, 'TELEGRAM_CHAT_ID', None)
        self.logger = logger.bind(name="TelegramBot")
        
        # API endpoint
        self.base_url = "https://api.telegram.org/bot"
        
        # Check if configured
        if not self.bot_token or not self.chat_id:
            self.logger.warning("Telegram bot not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
            self.enabled = False
        else:
            self.enabled = True
            self.logger.info("Telegram bot initialized")
    
    async def send_signal(self, signal: Dict) -> bool:
        """
        Send MMCI signal notification to Telegram.
        
        Args:
            signal: Signal dictionary with:
                - symbol: Stock symbol
                - direction: BUY/SELL/HOLD
                - consensus_score: MMCI score
                - risk_level: 1-5
                - reasoning: Signal reasoning
                - sector: Stock sector (optional)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        # Format message
        message = self._format_signal_message(signal)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{self.bot_token}/sendMessage"
                
                payload = {
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'Markdown',
                }
                
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        self.logger.info(f"Signal sent: {signal['symbol']} {signal['direction']}")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Telegram API error: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def _format_signal_message(self, signal: Dict) -> str:
        """Format signal into readable Telegram message."""
        symbol = signal.get('symbol', 'UNKNOWN')
        direction = signal.get('direction', 'HOLD')
        score = signal.get('consensus_score', 0.0)
        risk = signal.get('risk_level', 3)
        reasoning = signal.get('reasoning', '')[:200]  # Truncate long reasoning
        sector = signal.get('sector', 'N/A')
        
        # Emoji based on direction
        direction_emoji = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '🟡',
        }.get(direction, '⚪')
        
        # Risk stars
        risk_stars = '⭐' * risk
        
        # Format message
        message = f"""
{direction_emoji} *PAN THEON SIGNAL* {direction_emoji}

📈 *{symbol}*
🏢 *Sector:* {sector}
📊 *Direction:* {direction}
🎯 *MMCI Score:* {score:.3f}
⚠️ *Risk Level:* {risk_stars} ({risk}/5)

💡 *Reasoning:*
_{reasoning}_

─────────────────
🏛️ Project Pantheon MMCI
"""
        return message
    
    async def send_portfolio_update(self, portfolio: Dict) -> bool:
        """
        Send portfolio performance update.
        
        Args:
            portfolio: Portfolio dictionary with:
                - total_value: Current portfolio value
                - total_pnl: Total P&L
                - total_pnl_pct: P&L percentage
                - positions: Number of open positions
        """
        if not self.enabled:
            return False
        
        total_value = portfolio.get('total_value', 0)
        total_pnl = portfolio.get('total_pnl', 0)
        total_pnl_pct = portfolio.get('total_pnl_pct', 0)
        positions = portfolio.get('positions', 0)
        
        # Emoji based on P&L
        pnl_emoji = '📈' if total_pnl >= 0 else '📉'
        
        message = f"""
{pnl_emoji} *PORTFOLIO UPDATE* {pnl_emoji}

💰 *Total Value:* ₹{total_value:,.0f}
📊 *P&L:* ₹{total_pnl:,.0f} ({total_pnl_pct:+.2f}%)
📦 *Open Positions:* {positions}

─────────────────
🏛️ Project Pantheon
"""
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{self.bot_token}/sendMessage"
                
                payload = {
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'Markdown',
                }
                
                async with session.post(url, json=payload, timeout=10) as response:
                    return response.status == 200
                    
        except Exception as e:
            self.logger.error(f"Failed to send portfolio update: {e}")
            return False
    
    async def send_alert(self, title: str, message: str) -> bool:
        """
        Send custom alert message.
        
        Args:
            title: Alert title
            message: Alert message
        """
        if not self.enabled:
            return False
        
        formatted = f"""
⚠️ *{title}*

{message}

─────────────────
🏛️ Project Pantheon
"""
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{self.bot_token}/sendMessage"
                
                payload = {
                    'chat_id': self.chat_id,
                    'text': formatted,
                    'parse_mode': 'Markdown',
                }
                
                async with session.post(url, json=payload, timeout=10) as response:
                    return response.status == 200
                    
        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test Telegram bot connection."""
        if not self.enabled:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{self.bot_token}/getMe"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.info(f"Telegram bot connected: @{data['result']['username']}")
                        return True
                    else:
                        return False
                        
        except Exception as e:
            self.logger.error(f"Telegram connection test failed: {e}")
            return False


# Global bot instance
telegram_bot = TelegramSignalBot()


async def send_signal_notification(signal: Dict) -> bool:
    """Convenience function to send signal notification."""
    return await telegram_bot.send_signal(signal)


async def send_portfolio_notification(portfolio: Dict) -> bool:
    """Convenience function to send portfolio update."""
    return await telegram_bot.send_portfolio_update(portfolio)

"""
TikBot - TikTok Live Bot with Serena AI Integration
안정적이고 빠른 TikTok 라이브 방송 자동화 봇
"""

__version__ = "0.1.0"
__author__ = "TikBot Team"
__description__ = "TikTok Live Bot with AI Integration"

from .core.bot import TikBot
from .core.config import BotConfig
from .core.events import EventHandler

__all__ = ["TikBot", "BotConfig", "EventHandler"]
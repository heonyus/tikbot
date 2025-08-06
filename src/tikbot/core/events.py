"""
TikBot 이벤트 처리 시스템
"""

import asyncio
from enum import Enum
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime


class EventType(Enum):
    """이벤트 타입"""
    # TikTok Live 이벤트
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    COMMENT = "comment"
    GIFT = "gift"
    FOLLOW = "follow"
    SHARE = "share"
    LIKE = "like"
    JOIN = "join"
    
    # 봇 내부 이벤트
    BOT_START = "bot_start"
    BOT_STOP = "bot_stop"
    COMMAND = "command"
    AUTO_RESPONSE = "auto_response"
    SPAM_DETECTED = "spam_detected"
    
    # TTS 이벤트
    TTS_START = "tts_start"
    TTS_END = "tts_end"
    
    # 오버레이 이벤트
    OVERLAY_UPDATE = "overlay_update"


@dataclass
class Event:
    """이벤트 데이터"""
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CommentEvent(Event):
    """댓글 이벤트"""
    
    def __init__(self, username: str, nickname: str, comment: str, user_id: str, **kwargs):
        self.username = username
        self.nickname = nickname
        self.comment = comment
        self.user_id = user_id
        
        data = {
            "username": username,
            "nickname": nickname,
            "comment": comment,
            "user_id": user_id,
            **kwargs
        }
        super().__init__(EventType.COMMENT, data)


class GiftEvent(Event):
    """선물 이벤트"""
    
    def __init__(self, username: str, nickname: str, gift_name: str, 
                 gift_count: int, gift_id: int, **kwargs):
        self.username = username
        self.nickname = nickname
        self.gift_name = gift_name
        self.gift_count = gift_count
        self.gift_id = gift_id
        
        data = {
            "username": username,
            "nickname": nickname,
            "gift_name": gift_name,
            "gift_count": gift_count,
            "gift_id": gift_id,
            **kwargs
        }
        super().__init__(EventType.GIFT, data)


class FollowEvent(Event):
    """팔로우 이벤트"""
    
    def __init__(self, username: str, nickname: str, user_id: str, **kwargs):
        self.username = username
        self.nickname = nickname
        self.user_id = user_id
        
        data = {
            "username": username,
            "nickname": nickname,
            "user_id": user_id,
            **kwargs
        }
        super().__init__(EventType.FOLLOW, data)


class EventHandler:
    """이벤트 처리기"""
    
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
    
    def on(self, event_type: EventType):
        """이벤트 핸들러 데코레이터"""
        def decorator(func: Callable):
            self.add_handler(event_type, func)
            return func
        return decorator
    
    def add_handler(self, event_type: EventType, handler: Callable):
        """이벤트 핸들러 추가"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def remove_handler(self, event_type: EventType, handler: Callable):
        """이벤트 핸들러 제거"""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    async def emit(self, event: Event):
        """이벤트 발생"""
        # 이벤트 히스토리에 저장
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # 등록된 핸들러들 실행
        if event.type in self._handlers:
            tasks = []
            for handler in self._handlers[event.type]:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(event))
                else:
                    # 동기 함수를 비동기로 실행
                    tasks.append(asyncio.get_event_loop().run_in_executor(
                        None, handler, event
                    ))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def emit_simple(self, event_type: EventType, **data):
        """간단한 이벤트 발생"""
        event = Event(event_type, data)
        await self.emit(event)
    
    def get_event_history(self, event_type: Optional[EventType] = None, 
                          limit: int = 100) -> List[Event]:
        """이벤트 히스토리 조회"""
        history = self._event_history
        
        if event_type:
            history = [e for e in history if e.type == event_type]
        
        return history[-limit:] if limit else history
    
    def clear_history(self):
        """이벤트 히스토리 초기화"""
        self._event_history.clear()
    
    def get_handler_count(self, event_type: EventType) -> int:
        """특정 이벤트 타입의 핸들러 개수 반환"""
        return len(self._handlers.get(event_type, []))
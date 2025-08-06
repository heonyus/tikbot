"""
TikBot 메인 봇 클래스
"""

import asyncio
import re
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import (
    ConnectEvent, DisconnectEvent, CommentEvent as TikTokCommentEvent,
    GiftEvent as TikTokGiftEvent, FollowEvent as TikTokFollowEvent,
    ShareEvent, LikeEvent, JoinEvent
)

from .config import BotConfig
from .events import (
    EventHandler, EventType, Event, CommentEvent, 
    GiftEvent, FollowEvent
)


class TikBot:
    """TikTok Live Bot 메인 클래스"""
    
    def __init__(self, config: BotConfig, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.event_handler = EventHandler()
        
        # TikTok Live 클라이언트
        self.client: Optional[TikTokLiveClient] = None
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # 통계
        self.stats = {
            "messages_received": 0,
            "commands_processed": 0,
            "auto_responses_sent": 0,
            "gifts_received": 0,
            "followers_gained": 0,
            "spam_filtered": 0
        }
        
        # 봇 기능 모듈들
        self._tts_manager = None
        self._audio_manager = None
        self._music_manager = None
        self._overlay_manager = None
        
        # 내부 이벤트 핸들러 등록
        self._register_internal_handlers()
    
    def _register_internal_handlers(self):
        """내부 이벤트 핸들러 등록"""
        
        @self.event_handler.on(EventType.COMMENT)
        async def handle_comment(event: CommentEvent):
            self.stats["messages_received"] += 1
            
            # 스팸 필터링
            if self._is_spam(event.comment):
                self.stats["spam_filtered"] += 1
                await self.event_handler.emit_simple(
                    EventType.SPAM_DETECTED,
                    username=event.username,
                    comment=event.comment
                )
                return
            
            # 명령어 처리
            if event.comment.startswith('!') and self.config.features.command_processing:
                await self._process_command(event)
            
            # 자동 응답 처리
            elif self.config.features.auto_response:
                await self._process_auto_response(event)
            
            # TTS 처리
            if self._tts_manager and self.config.features.tts_enabled:
                await self._process_tts(event)
        
        @self.event_handler.on(EventType.GIFT)
        async def handle_gift(event: GiftEvent):
            self.stats["gifts_received"] += 1
            self.logger.info(
                f"🎁 {event.nickname}님이 {event.gift_name} x{event.gift_count} 선물!"
            )
        
        @self.event_handler.on(EventType.FOLLOW)
        async def handle_follow(event: FollowEvent):
            self.stats["followers_gained"] += 1
            if self.config.features.welcome_message:
                welcome_msg = f"🎉 {event.nickname}님 팔로우 감사합니다!"
                self.logger.info(welcome_msg)
    
    async def start(self):
        """봇 시작"""
        if self.is_running:
            return
        
        try:
            # TTS 매니저 초기화
            if self.config.features.tts_enabled:
                from ..tts.manager import TTSManager
                self._tts_manager = TTSManager(
                    config=self.config.tts.model_dump(),
                    logger=self.logger
                )
                await self._tts_manager.initialize()
            
            # Audio 매니저 초기화 (Sound Alerts)
            if self.config.features.sound_alerts_enabled:
                from ..audio.manager import AudioManager
                self._audio_manager = AudioManager(
                    config=self.config.audio.model_dump(),
                    logger=self.logger
                )
                await self._audio_manager.initialize()
                
                # 오디오 이벤트 핸들러 등록
                self._audio_manager.register_event_handlers(self.event_handler)
            
            # Music 매니저 초기화 (Spotify + YouTube)
            if self.config.features.music_enabled:
                from ..music.manager import MusicManager
                self._music_manager = MusicManager(
                    config=self.config.music.model_dump(),
                    logger=self.logger
                )
                await self._music_manager.initialize()
                
                # 음악 이벤트 핸들러 등록
                self._music_manager.register_event_handlers(self.event_handler)
            
            # Overlay 매니저 초기화 (Interactive Overlays)
            if self.config.features.overlay_enabled:
                from ..overlay.manager import OverlayManager
                self._overlay_manager = OverlayManager(
                    config=self.config.overlay.model_dump(),
                    logger=self.logger
                )
                await self._overlay_manager.initialize()
                
                # 오버레이 이벤트 핸들러 등록
                self._overlay_manager.register_event_handlers(self.event_handler)
            
            # TikTok Live 클라이언트 생성
            self.client = TikTokLiveClient(unique_id=self.config.tiktok.username)
            
            # TikTok Live 이벤트 핸들러 등록
            self._register_tiktok_handlers()
            
            # 봇 시작 이벤트 발생
            await self.event_handler.emit_simple(EventType.BOT_START)
            
            # TikTok Live 연결
            await self.client.connect()
            
            self.is_running = True
            self.start_time = datetime.now()
            
            self.logger.info(f"✅ TikBot이 @{self.config.tiktok.username}에 연결되었습니다!")
            
        except Exception as e:
            self.logger.error(f"❌ 봇 시작 실패: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """봇 종료"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # TikTok Live 연결 해제
        if self.client:
            try:
                await self.client.disconnect()
            except Exception as e:
                self.logger.error(f"TikTok Live 연결 해제 실패: {e}")
        
        # TTS 매니저 종료
        if self._tts_manager:
            await self._tts_manager.stop()
        
        # Audio 매니저 종료
        if self._audio_manager:
            await self._audio_manager.cleanup()
        
        # Music 매니저 종료
        if self._music_manager:
            await self._music_manager.cleanup()
        
        # Overlay 매니저 종료
        if self._overlay_manager:
            await self._overlay_manager.cleanup()
        
        # 봇 종료 이벤트 발생
        await self.event_handler.emit_simple(EventType.BOT_STOP)
        
        # 통계 출력
        if self.start_time:
            runtime = datetime.now() - self.start_time
            self.logger.info(f"📊 봇 실행 시간: {runtime}")
            self.logger.info(f"📊 처리한 메시지: {self.stats['messages_received']}")
            self.logger.info(f"📊 받은 선물: {self.stats['gifts_received']}")
        
        self.logger.info("🔴 TikBot이 종료되었습니다.")
    
    def _register_tiktok_handlers(self):
        """TikTok Live 이벤트 핸들러 등록"""
        
        @self.client.on(ConnectEvent)
        async def on_connect(event):
            self.logger.info("🟢 TikTok Live에 연결되었습니다!")
            await self.event_handler.emit_simple(
                EventType.CONNECT,
                room_id=event.room_id if hasattr(event, 'room_id') else None
            )
        
        @self.client.on(DisconnectEvent)
        async def on_disconnect(event):
            self.logger.warning("🟡 TikTok Live 연결이 끊어졌습니다.")
            await self.event_handler.emit_simple(EventType.DISCONNECT)
            
            # 자동 재연결
            if self.config.tiktok.auto_reconnect and self.is_running:
                self.logger.info(f"{self.config.tiktok.reconnect_delay}초 후 재연결 시도...")
                await asyncio.sleep(self.config.tiktok.reconnect_delay)
                if self.is_running:
                    try:
                        await self.client.connect()
                    except Exception as e:
                        self.logger.error(f"재연결 실패: {e}")
        
        @self.client.on(TikTokCommentEvent)
        async def on_comment(event):
            comment_event = CommentEvent(
                username=event.user.unique_id,
                nickname=event.user.nickname,
                comment=event.comment,
                user_id=str(event.user.user_id)
            )
            await self.event_handler.emit(comment_event)
        
        @self.client.on(TikTokGiftEvent)
        async def on_gift(event):
            gift_event = GiftEvent(
                username=event.user.unique_id,
                nickname=event.user.nickname,
                gift_name=event.gift.name,
                gift_count=event.gift.count,
                gift_id=event.gift.id
            )
            await self.event_handler.emit(gift_event)
        
        @self.client.on(TikTokFollowEvent)
        async def on_follow(event):
            follow_event = FollowEvent(
                username=event.user.unique_id,
                nickname=event.user.nickname,
                user_id=str(event.user.user_id)
            )
            await self.event_handler.emit(follow_event)
        
        @self.client.on(ShareEvent)
        async def on_share(event):
            await self.event_handler.emit_simple(
                EventType.SHARE,
                username=event.user.unique_id,
                nickname=event.user.nickname
            )
        
        @self.client.on(LikeEvent)
        async def on_like(event):
            await self.event_handler.emit_simple(
                EventType.LIKE,
                username=event.user.unique_id,
                nickname=event.user.nickname,
                like_count=event.count if hasattr(event, 'count') else 1
            )
        
        @self.client.on(JoinEvent)
        async def on_join(event):
            await self.event_handler.emit_simple(
                EventType.JOIN,
                username=event.user.unique_id,
                nickname=event.user.nickname
            )
    
    def _is_spam(self, message: str) -> bool:
        """스팸 메시지 감지"""
        if not self.config.features.spam_filter:
            return False
        
        message_lower = message.lower()
        return any(keyword.lower() in message_lower for keyword in self.config.spam_keywords)
    
    async def _process_command(self, event: CommentEvent):
        """명령어 처리"""
        command = event.comment.split()[0].lower()
        
        if command in self.config.commands:
            response = self.config.commands[command]
            
            # 특별 명령어 처리
            if command == "!time" and self.start_time:
                runtime = datetime.now() - self.start_time
                response = f"현재 방송 시간: {str(runtime).split('.')[0]}"
            elif command == "!stats":
                response = (
                    f"📊 통계 - 메시지: {self.stats['messages_received']}, "
                    f"선물: {self.stats['gifts_received']}, "
                    f"팔로워: {self.stats['followers_gained']}"
                )
            elif command == "!commands":
                cmd_list = ", ".join(list(self.config.commands.keys())[:8])  # 처음 8개만
                response = f"🤖 사용 가능한 명령어: {cmd_list}"
            
            self.stats["commands_processed"] += 1
            await self.event_handler.emit_simple(
                EventType.COMMAND,
                username=event.username,
                command=command,
                response=response
            )
            
            self.logger.info(f"🤖 명령어 응답 [{event.nickname}]: {response}")
    
    async def _process_auto_response(self, event: CommentEvent):
        """자동 응답 처리"""
        message = event.comment.lower()
        
        for keyword, responses in self.config.auto_responses.items():
            if keyword.lower() in message:
                import random
                response = random.choice(responses)
                
                self.stats["auto_responses_sent"] += 1
                await self.event_handler.emit_simple(
                    EventType.AUTO_RESPONSE,
                    username=event.username,
                    keyword=keyword,
                    response=response
                )
                
                self.logger.info(f"💬 자동 응답 [{event.nickname}]: {response}")
                break
    
    async def _process_tts(self, event: CommentEvent):
        """TTS 처리"""
        if not self._tts_manager:
            return
        
        # TTS 명령어 체크 (!tts)
        if event.comment.startswith('!tts '):
            text = event.comment[5:].strip()
            if text:
                success = await self._tts_manager.request_tts(
                    text=text, 
                    username=event.username,
                    priority=1  # 명령어는 높은 우선순위
                )
                if success:
                    self.logger.info(f"🔊 TTS 요청: {text} (by {event.nickname})")
        
        # 일반 채팅 TTS (설정에 따라)
        elif hasattr(self.config.tts, 'auto_read_chat') and self.config.tts.auto_read_chat:
            # 길이 제한 및 필터 적용
            if 5 <= len(event.comment) <= 50:
                await self._tts_manager.request_tts(
                    text=event.comment,
                    username=event.username,
                    priority=2  # 일반 채팅은 보통 우선순위
                )
    
    def get_stats(self) -> Dict[str, Any]:
        """봇 통계 반환"""
        stats = self.stats.copy()
        if self.start_time:
            stats["uptime"] = str(datetime.now() - self.start_time).split('.')[0]
            stats["start_time"] = self.start_time.isoformat()
        stats["is_running"] = self.is_running
        return stats
    
    def add_command(self, command: str, response: str):
        """명령어 추가"""
        self.config.commands[command] = response
    
    def remove_command(self, command: str):
        """명령어 제거"""
        if command in self.config.commands:
            del self.config.commands[command]
    
    def add_auto_response(self, keyword: str, responses: list):
        """자동 응답 추가"""
        self.config.auto_responses[keyword] = responses
    
    def remove_auto_response(self, keyword: str):
        """자동 응답 제거"""
        if keyword in self.config.auto_responses:
            del self.config.auto_responses[keyword]
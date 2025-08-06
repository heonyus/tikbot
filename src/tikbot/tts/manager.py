"""
TTS 매니저 - TTS 기능을 관리하고 제어
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from queue import Queue
from dataclasses import dataclass

from .engine import TTSEngine, create_tts_engine
from ..core.events import EventHandler, EventType


@dataclass
class TTSRequest:
    """TTS 요청 데이터"""
    text: str
    username: str = ""
    priority: int = 1  # 1=높음, 2=보통, 3=낮음
    

class TTSManager:
    """TTS 매니저 클래스"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.engine: Optional[TTSEngine] = None
        self.enabled = config.get('enabled', False)
        
        # TTS 큐
        self.tts_queue = asyncio.Queue(maxsize=50)
        self.is_processing = False
        
        # 필터 설정
        self.max_length = config.get('max_length', 100)
        self.min_length = config.get('min_length', 1)
        self.blocked_words = set(config.get('blocked_words', []))
        self.vip_users = set(config.get('vip_users', []))
        
        # 통계
        self.stats = {
            "total_requests": 0,
            "successful_plays": 0,
            "filtered_messages": 0,
            "queue_full_drops": 0
        }
    
    async def initialize(self):
        """TTS 엔진 초기화"""
        if not self.enabled:
            self.logger.info("TTS 기능이 비활성화되어 있습니다.")
            return
        
        try:
            engine_type = self.config.get('engine', 'pyttsx3')
            self.engine = create_tts_engine(
                engine_type=engine_type,
                language=self.config.get('language', 'ko'),
                logger=self.logger
            )
            
            if self.engine:
                # 엔진 설정 적용
                rate = self.config.get('voice_rate', 150)
                volume = self.config.get('voice_volume', 0.8)
                
                self.engine.set_voice_rate(rate)
                self.engine.set_voice_volume(volume)
                
                self.logger.info(f"TTS 엔진 초기화 완료: {engine_type}")
                
                # TTS 처리 태스크 시작
                asyncio.create_task(self._process_tts_queue())
            else:
                self.logger.warning("TTS 엔진을 초기화할 수 없습니다.")
                
        except Exception as e:
            self.logger.error(f"TTS 초기화 실패: {e}")
            self.enabled = False
    
    async def request_tts(self, text: str, username: str = "", priority: int = 2) -> bool:
        """TTS 요청 추가"""
        if not self.enabled or not self.engine:
            return False
        
        self.stats["total_requests"] += 1
        
        # 텍스트 필터링
        if not self._is_text_valid(text, username):
            self.stats["filtered_messages"] += 1
            return False
        
        # 큐에 추가
        request = TTSRequest(text=text, username=username, priority=priority)
        
        try:
            self.tts_queue.put_nowait(request)
            return True
        except asyncio.QueueFull:
            self.stats["queue_full_drops"] += 1
            self.logger.warning("TTS 큐가 가득참. 요청을 버립니다.")
            return False
    
    def _is_text_valid(self, text: str, username: str) -> bool:
        """텍스트 유효성 검사"""
        # 길이 체크
        if len(text) < self.min_length or len(text) > self.max_length:
            return False
        
        # 금지어 체크
        text_lower = text.lower()
        if any(word in text_lower for word in self.blocked_words):
            return False
        
        # URL 체크
        if 'http' in text_lower or 'www.' in text_lower:
            return False
        
        # 숫자만 있는 메시지 필터
        if text.replace(' ', '').isdigit():
            return False
        
        return True
    
    async def _process_tts_queue(self):
        """TTS 큐 처리 루프"""
        self.is_processing = True
        
        while self.enabled and self.engine:
            try:
                # 우선순위가 높은 요청부터 처리
                request = await asyncio.wait_for(self.tts_queue.get(), timeout=1.0)
                
                # VIP 사용자는 우선순위 높임
                if request.username in self.vip_users:
                    request.priority = 1
                
                # TTS 실행
                success = await self.engine.speak(request.text)
                
                if success:
                    self.stats["successful_plays"] += 1
                    self.logger.info(f"TTS 재생: {request.text[:30]}... (by {request.username})")
                
                # 작업 완료 표시
                self.tts_queue.task_done()
                
                # 다음 요청 전 잠시 대기
                await asyncio.sleep(0.5)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"TTS 처리 중 오류: {e}")
                await asyncio.sleep(1)
        
        self.is_processing = False
    
    def update_config(self, config: Dict[str, Any]):
        """설정 업데이트"""
        self.config.update(config)
        
        if self.engine:
            if 'voice_rate' in config:
                self.engine.set_voice_rate(config['voice_rate'])
            if 'voice_volume' in config:
                self.engine.set_voice_volume(config['voice_volume'])
        
        self.enabled = config.get('enabled', self.enabled)
        self.max_length = config.get('max_length', self.max_length)
        self.min_length = config.get('min_length', self.min_length)
        
        if 'blocked_words' in config:
            self.blocked_words = set(config['blocked_words'])
        if 'vip_users' in config:
            self.vip_users = set(config['vip_users'])
    
    def add_vip_user(self, username: str):
        """VIP 사용자 추가"""
        self.vip_users.add(username)
    
    def remove_vip_user(self, username: str):
        """VIP 사용자 제거"""
        self.vip_users.discard(username)
    
    def clear_queue(self):
        """TTS 큐 비우기"""
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
                self.tts_queue.task_done()
            except asyncio.QueueEmpty:
                break
    
    def get_queue_size(self) -> int:
        """현재 큐 크기 반환"""
        return self.tts_queue.qsize()
    
    def get_stats(self) -> Dict[str, Any]:
        """TTS 통계 반환"""
        stats = self.stats.copy()
        stats.update({
            "enabled": self.enabled,
            "queue_size": self.get_queue_size(),
            "is_processing": self.is_processing,
            "engine_type": self.config.get('engine', 'none')
        })
        return stats
    
    async def stop(self):
        """TTS 매니저 종료"""
        self.enabled = False
        self.clear_queue()
        
        # 처리 중인 작업 완료 대기
        if self.is_processing:
            await asyncio.sleep(2)
        
        self.logger.info("TTS 매니저가 종료되었습니다.")
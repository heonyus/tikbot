"""
오디오 매니저 - 전체 오디오 시스템 통합 관리
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

from .player import AudioPlayer
from .alerts import SoundAlerts, AlertType, SoundAlert
from ..core.events import EventHandler, EventType


class AudioManager:
    """오디오 시스템 통합 매니저"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.enabled = config.get('enabled', True)
        
        # 컴포넌트 초기화
        self.player: Optional[AudioPlayer] = None
        self.sound_alerts: Optional[SoundAlerts] = None
        
        # 설정
        self.global_volume = config.get('global_volume', 0.7)
        self.sounds_directory = Path(config.get('sounds_directory', 'static/sounds'))
        
        # 통계
        self.stats = {
            "initialization_time": None,
            "total_sounds_played": 0,
            "alerts_triggered": 0,
            "errors_count": 0
        }
    
    async def initialize(self) -> bool:
        """오디오 시스템 초기화"""
        if not self.enabled:
            self.logger.info("오디오 시스템이 비활성화되어 있습니다.")
            return True
        
        try:
            import time
            start_time = time.time()
            
            # 사운드 디렉토리 생성
            self.sounds_directory.mkdir(parents=True, exist_ok=True)
            
            # 오디오 플레이어 초기화
            self.player = AudioPlayer(logger=self.logger)
            if not self.player.is_available():
                self.logger.warning("오디오 플레이어를 사용할 수 없습니다.")
                return False
            
            # 전역 볼륨 설정
            self.player.set_volume(self.global_volume)
            
            # Sound Alerts 초기화
            alerts_config = self.config.get('sound_alerts', {})
            alerts_config['sounds_directory'] = str(self.sounds_directory)
            
            self.sound_alerts = SoundAlerts(
                config=alerts_config,
                logger=self.logger
            )
            
            # 초기화 시간 기록
            self.stats["initialization_time"] = time.time() - start_time
            
            self.logger.info(f"🎵 오디오 시스템 초기화 완료 ({self.stats['initialization_time']:.2f}초)")
            
            # 기본 사운드 파일 생성 (없는 경우)
            await self._create_default_sounds()
            
            return True
            
        except Exception as e:
            self.logger.error(f"오디오 시스템 초기화 실패: {e}")
            self.stats["errors_count"] += 1
            return False
    
    async def _create_default_sounds(self):
        """기본 사운드 파일들 생성 (간단한 beep 사운드)"""
        try:
            # pygame이 있는 경우에만 기본 사운드 생성
            if not self.player or not hasattr(self.player, 'engine') or self.player.engine != 'pygame':
                return
            
            import pygame
            import numpy as np
            
            # 기본 사운드 파일들 정의
            default_sounds = {
                'follow.wav': (800, 0.3),      # 팔로우: 높은 톤
                'gift.wav': (600, 0.5),        # 선물: 중간 톤
                'big_gift.wav': (400, 0.8),    # 큰 선물: 낮은 톤
                'comment.wav': (1000, 0.2),    # 댓글: 매우 높은 톤
                'like.wav': (1200, 0.1),       # 좋아요: 짧은 높은 톤
                'join.wav': (500, 0.4),        # 입장: 따뜻한 톤
                'command.wav': (700, 0.2),     # 명령어: 중간-높은 톤
            }
            
            for filename, (frequency, duration) in default_sounds.items():
                file_path = self.sounds_directory / filename
                
                # 파일이 이미 존재하면 건너뛰기
                if file_path.exists():
                    continue
                
                try:
                    # 간단한 사인파 생성
                    sample_rate = 22050
                    samples = int(sample_rate * duration)
                    
                    # 사인파 생성
                    t = np.linspace(0, duration, samples, False)
                    wave = np.sin(2 * np.pi * frequency * t)
                    
                    # 페이드 아웃 효과
                    fade_samples = int(sample_rate * 0.05)  # 50ms 페이드
                    if fade_samples < samples:
                        fade = np.linspace(1, 0, fade_samples)
                        wave[-fade_samples:] *= fade
                    
                    # 16비트 정수로 변환
                    wave = (wave * 32767).astype(np.int16)
                    
                    # 스테레오로 변환
                    stereo_wave = np.zeros((samples, 2), dtype=np.int16)
                    stereo_wave[:, 0] = wave
                    stereo_wave[:, 1] = wave
                    
                    # pygame Sound 객체로 변환 후 저장
                    sound = pygame.sndarray.make_sound(stereo_wave)
                    pygame.mixer.Sound.save(sound, str(file_path))
                    
                    self.logger.debug(f"기본 사운드 생성: {filename}")
                    
                except Exception as e:
                    self.logger.warning(f"기본 사운드 생성 실패 {filename}: {e}")
            
        except ImportError:
            self.logger.info("numpy가 없어 기본 사운드를 생성할 수 없습니다.")
        except Exception as e:
            self.logger.warning(f"기본 사운드 생성 중 오류: {e}")
    
    async def play_sound(self, file_path: str, volume: Optional[float] = None) -> bool:
        """사운드 파일 재생"""
        if not self.enabled or not self.player:
            return False
        
        try:
            success = await self.player.play_sound(file_path, volume)
            if success:
                self.stats["total_sounds_played"] += 1
            return success
        except Exception as e:
            self.logger.error(f"사운드 재생 실패: {e}")
            self.stats["errors_count"] += 1
            return False
    
    async def trigger_alert(self, event_type: EventType, event_data: Dict[str, Any] = None) -> bool:
        """이벤트 알림 트리거"""
        if not self.enabled or not self.sound_alerts:
            return False
        
        try:
            success = await self.sound_alerts.trigger_alert(event_type, event_data)
            if success:
                self.stats["alerts_triggered"] += 1
            return success
        except Exception as e:
            self.logger.error(f"알림 트리거 실패: {e}")
            self.stats["errors_count"] += 1
            return False
    
    def register_event_handlers(self, event_handler: EventHandler):
        """이벤트 핸들러에 오디오 이벤트 등록"""
        if not self.enabled:
            return
        
        @event_handler.on(EventType.FOLLOW)
        async def on_follow_audio(event_data):
            await self.trigger_alert(EventType.FOLLOW, event_data)
        
        @event_handler.on(EventType.GIFT) 
        async def on_gift_audio(event_data):
            await self.trigger_alert(EventType.GIFT, event_data)
        
        @event_handler.on(EventType.COMMENT)
        async def on_comment_audio(event_data):
            # 댓글은 너무 빈번하므로 설정에 따라 제한
            if self.config.get('sound_alerts', {}).get('comment_alerts', False):
                await self.trigger_alert(EventType.COMMENT, event_data)
        
        @event_handler.on(EventType.LIKE)
        async def on_like_audio(event_data):
            # 좋아요도 빈번하므로 설정에 따라 제한
            if self.config.get('sound_alerts', {}).get('like_alerts', False):
                await self.trigger_alert(EventType.LIKE, event_data)
        
        @event_handler.on(EventType.JOIN)
        async def on_join_audio(event_data):
            await self.trigger_alert(EventType.JOIN, event_data)
        
        @event_handler.on(EventType.COMMAND)
        async def on_command_audio(event_data):
            # 특정 명령어에만 사운드 재생
            command_sounds = self.config.get('sound_alerts', {}).get('command_sounds', [])
            command = event_data.get('command', '')
            if command in command_sounds:
                await self.trigger_alert(EventType.COMMAND, event_data)
        
        self.logger.info("오디오 이벤트 핸들러 등록 완료")
    
    def add_custom_alert(self, alert_type: str, name: str, file_path: str, 
                        volume: float = 0.7, cooldown: int = 0, 
                        conditions: Dict[str, Any] = None) -> bool:
        """사용자 정의 알림 추가"""
        if not self.sound_alerts:
            return False
        
        try:
            alert_type_enum = AlertType(alert_type)
            alert = SoundAlert(
                name=name,
                file_path=file_path,
                volume=volume,
                cooldown=cooldown,
                conditions=conditions or {}
            )
            
            self.sound_alerts.add_custom_alert(alert_type_enum, alert)
            return True
            
        except (ValueError, Exception) as e:
            self.logger.error(f"사용자 정의 알림 추가 실패: {e}")
            return False
    
    def set_global_volume(self, volume: float):
        """전역 볼륨 설정"""
        self.global_volume = max(0.0, min(1.0, volume))
        
        if self.player:
            self.player.set_volume(self.global_volume)
        
        if self.sound_alerts:
            self.sound_alerts.set_global_volume(self.global_volume)
    
    def get_volume(self) -> float:
        """현재 볼륨 반환"""
        return self.global_volume
    
    def set_enabled(self, enabled: bool):
        """오디오 시스템 활성화/비활성화"""
        self.enabled = enabled
        self.logger.info(f"오디오 시스템 {'활성화' if enabled else '비활성화'}")
    
    def stop_all_sounds(self):
        """모든 사운드 중지"""
        if self.player:
            self.player.stop_all()
        
        if self.sound_alerts:
            self.sound_alerts.stop_all_sounds()
    
    def get_stats(self) -> Dict[str, Any]:
        """통합 통계 반환"""
        stats = self.stats.copy()
        
        if self.player:
            stats["player_available"] = self.player.is_available()
            stats["supported_formats"] = self.player.get_supported_formats()
        
        if self.sound_alerts:
            alerts_stats = self.sound_alerts.get_stats()
            stats.update({f"alerts_{k}": v for k, v in alerts_stats.items()})
        
        stats.update({
            "enabled": self.enabled,
            "global_volume": self.global_volume,
            "sounds_directory": str(self.sounds_directory)
        })
        
        return stats
    
    def list_available_sounds(self) -> List[Dict[str, Any]]:
        """사용 가능한 사운드 파일 목록"""
        sounds = []
        
        if not self.sounds_directory.exists():
            return sounds
        
        for file_path in self.sounds_directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.wav', '.mp3', '.ogg']:
                sounds.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "format": file_path.suffix.lower()
                })
        
        return sounds
    
    async def cleanup(self):
        """리소스 정리"""
        if self.sound_alerts:
            self.sound_alerts.cleanup()
        
        if self.player:
            self.player.cleanup()
        
        self.logger.info("오디오 매니저 정리 완료")
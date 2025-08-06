"""
오디오 플레이어 - 효과음 재생 엔진
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from queue import Queue
import threading

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# playsound는 Windows에서 빌드 문제가 있어 제거
PLAYSOUND_AVAILABLE = False


class AudioPlayer:
    """오디오 플레이어 클래스"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.is_initialized = False
        self.current_volume = 0.7
        self.sound_queue = Queue(maxsize=10)
        self.is_playing = False
        
        # 지원 가능한 엔진 확인
        self.available_engines = []
        if PYGAME_AVAILABLE:
            self.available_engines.append("pygame")
        if PLAYSOUND_AVAILABLE:
            self.available_engines.append("playsound")
        
        # 기본 엔진 선택
        self.engine = self.available_engines[0] if self.available_engines else None
        
        if not self.engine:
            self.logger.warning("사용 가능한 오디오 엔진이 없습니다.")
            return
        
        self._initialize_engine()
    
    def _initialize_engine(self):
        """오디오 엔진 초기화"""
        try:
            if self.engine == "pygame":
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.music.set_volume(self.current_volume)
                self.logger.info("🎵 Pygame 오디오 엔진 초기화 완료")
            
            self.is_initialized = True
            
        except Exception as e:
            self.logger.error(f"오디오 엔진 초기화 실패: {e}")
            self.is_initialized = False
    
    async def play_sound(self, file_path: str, volume: Optional[float] = None) -> bool:
        """
        사운드 파일 재생
        
        Args:
            file_path: 재생할 오디오 파일 경로
            volume: 볼륨 (0.0-1.0), None이면 기본 볼륨 사용
        
        Returns:
            재생 성공 여부
        """
        if not self.is_initialized:
            self.logger.warning("오디오 엔진이 초기화되지 않았습니다.")
            return False
        
        file_path = Path(file_path)
        if not file_path.exists():
            self.logger.error(f"오디오 파일을 찾을 수 없습니다: {file_path}")
            return False
        
        try:
            if volume is not None:
                original_volume = self.current_volume
                self.set_volume(volume)
            
            success = await self._play_with_engine(str(file_path))
            
            if volume is not None:
                self.set_volume(original_volume)
            
            return success
            
        except Exception as e:
            self.logger.error(f"사운드 재생 실패: {e}")
            return False
    
    async def _play_with_engine(self, file_path: str) -> bool:
        """엔진별 재생 로직"""
        try:
            if self.engine == "pygame":
                return await self._play_with_pygame(file_path)
            elif self.engine == "playsound":
                return await self._play_with_playsound(file_path)
            else:
                return False
        except Exception as e:
            self.logger.error(f"엔진 재생 실패: {e}")
            return False
    
    async def _play_with_pygame(self, file_path: str) -> bool:
        """Pygame으로 재생"""
        def _play():
            try:
                # 효과음으로 재생 (배경음악과 별개)
                sound = pygame.mixer.Sound(file_path)
                sound.set_volume(self.current_volume)
                channel = sound.play()
                
                # 재생 완료까지 대기
                while channel.get_busy():
                    pygame.time.wait(10)
                
                return True
            except Exception as e:
                self.logger.error(f"Pygame 재생 오류: {e}")
                return False
        
        # 별도 스레드에서 실행
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _play)
        return result
    
    async def _play_with_playsound(self, file_path: str) -> bool:
        """playsound로 재생"""
        def _play():
            try:
                playsound.playsound(file_path, block=True)
                return True
            except Exception as e:
                self.logger.error(f"Playsound 재생 오류: {e}")
                return False
        
        # 별도 스레드에서 실행
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _play)
        return result
    
    def set_volume(self, volume: float):
        """볼륨 설정 (0.0-1.0)"""
        self.current_volume = max(0.0, min(1.0, volume))
        
        if self.engine == "pygame" and self.is_initialized:
            try:
                pygame.mixer.music.set_volume(self.current_volume)
            except:
                pass
    
    def get_volume(self) -> float:
        """현재 볼륨 반환"""
        return self.current_volume
    
    def stop_all(self):
        """모든 재생 중지"""
        if self.engine == "pygame" and self.is_initialized:
            try:
                pygame.mixer.stop()
            except:
                pass
    
    def is_available(self) -> bool:
        """오디오 플레이어 사용 가능 여부"""
        return self.is_initialized and self.engine is not None
    
    def get_supported_formats(self) -> list:
        """지원하는 오디오 포맷 목록"""
        if self.engine == "pygame":
            return [".wav", ".ogg", ".mp3"]
        elif self.engine == "playsound":
            return [".wav", ".mp3"]
        else:
            return []
    
    def cleanup(self):
        """리소스 정리"""
        if self.engine == "pygame" and self.is_initialized:
            try:
                pygame.mixer.quit()
            except:
                pass
        
        self.is_initialized = False
        self.logger.info("오디오 플레이어 정리 완료")
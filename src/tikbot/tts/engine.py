"""
TTS 엔진 구현
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    from gtts import gTTS
    import pygame
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


class TTSEngine(ABC):
    """TTS 엔진 베이스 클래스"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.is_speaking = False
    
    @abstractmethod
    async def speak(self, text: str) -> bool:
        """텍스트를 음성으로 변환하여 재생"""
        pass
    
    @abstractmethod
    def set_voice_rate(self, rate: int):
        """음성 속도 설정"""
        pass
    
    @abstractmethod 
    def set_voice_volume(self, volume: float):
        """음성 볼륨 설정"""
        pass


class PyttsxEngine(TTSEngine):
    """pyttsx3 기반 TTS 엔진"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__(logger)
        
        if not PYTTSX3_AVAILABLE:
            raise ImportError("pyttsx3가 설치되지 않았습니다.")
        
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 0.8)
            
            # 한국어 음성 찾기
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'korea' in voice.name.lower() or 'ko-' in voice.id.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
                    
        except Exception as e:
            self.logger.error(f"pyttsx3 초기화 실패: {e}")
            raise
    
    async def speak(self, text: str) -> bool:
        """텍스트 음성 재생"""
        if self.is_speaking:
            return False
        
        try:
            self.is_speaking = True
            
            # 별도 스레드에서 음성 재생
            def _speak():
                self.engine.say(text)
                self.engine.runAndWait()
            
            await asyncio.get_event_loop().run_in_executor(None, _speak)
            return True
            
        except Exception as e:
            self.logger.error(f"TTS 재생 실패: {e}")
            return False
        finally:
            self.is_speaking = False
    
    def set_voice_rate(self, rate: int):
        """음성 속도 설정 (50-300)"""
        self.engine.setProperty('rate', max(50, min(300, rate)))
    
    def set_voice_volume(self, volume: float):
        """음성 볼륨 설정 (0.0-1.0)"""
        self.engine.setProperty('volume', max(0.0, min(1.0, volume)))


class GTTSEngine(TTSEngine):
    """Google TTS 기반 엔진"""
    
    def __init__(self, language: str = 'ko', logger: Optional[logging.Logger] = None):
        super().__init__(logger)
        
        if not GTTS_AVAILABLE:
            raise ImportError("gtts와 pygame이 설치되지 않았습니다.")
        
        self.language = language
        self.temp_dir = Path("temp_audio")
        self.temp_dir.mkdir(exist_ok=True)
        
        # pygame 초기화
        try:
            pygame.mixer.init()
        except Exception as e:
            self.logger.error(f"pygame 초기화 실패: {e}")
            raise
    
    async def speak(self, text: str) -> bool:
        """텍스트 음성 재생"""
        if self.is_speaking:
            return False
        
        try:
            self.is_speaking = True
            
            # 임시 파일 경로
            temp_file = self.temp_dir / f"tts_{hash(text)}.mp3"
            
            # gTTS로 음성 파일 생성
            def _create_audio():
                tts = gTTS(text=text, lang=self.language, slow=False)
                tts.save(str(temp_file))
            
            await asyncio.get_event_loop().run_in_executor(None, _create_audio)
            
            # pygame으로 재생
            def _play_audio():
                pygame.mixer.music.load(str(temp_file))
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
            
            await asyncio.get_event_loop().run_in_executor(None, _play_audio)
            
            # 임시 파일 삭제
            if temp_file.exists():
                temp_file.unlink()
            
            return True
            
        except Exception as e:
            self.logger.error(f"gTTS 재생 실패: {e}")
            return False
        finally:
            self.is_speaking = False
    
    def set_voice_rate(self, rate: int):
        """gTTS는 속도 조절 미지원"""
        pass
    
    def set_voice_volume(self, volume: float):
        """pygame 볼륨 설정"""
        try:
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
        except:
            pass


def create_tts_engine(engine_type: str = "pyttsx3", **kwargs) -> Optional[TTSEngine]:
    """TTS 엔진 팩토리 함수"""
    
    try:
        if engine_type.lower() == "pyttsx3" and PYTTSX3_AVAILABLE:
            return PyttsxEngine(**kwargs)
        elif engine_type.lower() == "gtts" and GTTS_AVAILABLE:
            return GTTSEngine(**kwargs)
        else:
            # 사용 가능한 엔진 자동 선택
            if PYTTSX3_AVAILABLE:
                return PyttsxEngine(**kwargs)
            elif GTTS_AVAILABLE:
                return GTTSEngine(**kwargs)
            else:
                return None
                
    except Exception as e:
        logger = kwargs.get('logger', logging.getLogger(__name__))
        logger.error(f"TTS 엔진 생성 실패: {e}")
        return None
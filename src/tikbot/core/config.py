"""
TikBot 설정 관리
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import yaml


class TikTokConfig(BaseModel):
    """TikTok 연결 설정"""
    username: str = Field(description="TikTok 사용자명 (@제외)")
    session_id: Optional[str] = Field(default=None, description="세션 ID (선택사항)")
    room_id: Optional[str] = Field(default=None, description="방 ID (선택사항)")
    auto_reconnect: bool = Field(default=True, description="자동 재연결 여부")
    reconnect_delay: int = Field(default=5, description="재연결 대기 시간(초)")


class BotFeatures(BaseModel):
    """봇 기능 설정"""
    auto_response: bool = Field(default=True, description="자동 응답 활성화")
    welcome_message: bool = Field(default=True, description="환영 메시지 활성화") 
    tts_enabled: bool = Field(default=False, description="TTS 기능 활성화")
    sound_alerts_enabled: bool = Field(default=True, description="Sound Alerts 활성화")
    music_enabled: bool = Field(default=True, description="Music Integration 활성화")
    overlay_enabled: bool = Field(default=False, description="오버레이 활성화")
    spam_filter: bool = Field(default=True, description="스팸 필터 활성화")
    command_processing: bool = Field(default=True, description="명령어 처리 활성화")


class TTSConfig(BaseModel):
    """TTS 설정"""
    engine: str = Field(default="pyttsx3", description="TTS 엔진 (pyttsx3, gtts, azure)")
    voice_rate: int = Field(default=150, description="음성 속도")
    voice_volume: float = Field(default=0.8, description="음성 볼륨 (0.0-1.0)")
    language: str = Field(default="ko", description="언어 코드")
    # Azure TTS 설정 (선택사항)
    azure_key: Optional[str] = Field(default=None, description="Azure Speech API 키")
    azure_region: Optional[str] = Field(default=None, description="Azure 지역")


class OverlayConfig(BaseModel):
    """오버레이 설정"""
    enabled: bool = Field(default=True, description="오버레이 시스템 활성화")
    websocket_host: str = Field(default="localhost", description="WebSocket 서버 호스트")
    websocket_port: int = Field(default=8080, description="WebSocket 서버 포트")
    templates_dir: str = Field(default="templates", description="템플릿 디렉토리")
    static_dir: str = Field(default="static", description="정적 파일 디렉토리")
    
    # 기존 설정들 (하위 호환성)
    width: int = Field(default=800, description="오버레이 너비")
    height: int = Field(default=600, description="오버레이 높이")
    chat_font_size: int = Field(default=16, description="채팅 폰트 크기")
    max_messages: int = Field(default=20, description="최대 표시 메시지 수")
    background_color: str = Field(default="rgba(0,0,0,0.7)", description="배경색")
    text_color: str = Field(default="#FFFFFF", description="텍스트 색상")


class APIConfig(BaseModel):
    """API 서버 설정"""
    enabled: bool = Field(default=True, description="API 서버 활성화")
    host: str = Field(default="localhost", description="호스트 주소")
    port: int = Field(default=8000, description="포트 번호")
    cors_origins: List[str] = Field(default=["*"], description="CORS 허용 도메인")


class AudioConfig(BaseModel):
    """오디오 및 Sound Alerts 설정"""
    enabled: bool = Field(default=True, description="오디오 시스템 활성화")
    global_volume: float = Field(default=0.7, description="전역 볼륨 (0.0-1.0)")
    sounds_directory: str = Field(default="static/sounds", description="사운드 파일 디렉토리")
    
    # Sound Alerts 설정
    sound_alerts: Dict[str, Any] = Field(default_factory=lambda: {
        "comment_alerts": False,
        "like_alerts": False,
        "command_sounds": ["!effect", "!sound"],
        "custom_alerts": {}
    })


class MusicConfig(BaseModel):
    """Music Integration 설정"""
    enabled: bool = Field(default=True, description="음악 시스템 활성화")
    auto_play: bool = Field(default=True, description="자동 재생")
    allow_explicit: bool = Field(default=False, description="성인 콘텐츠 허용")
    max_queue_size: int = Field(default=50, description="최대 큐 크기")
    max_duration: int = Field(default=600, description="최대 곡 길이 (초)")
    max_requests_per_user: int = Field(default=3, description="사용자당 최대 요청 수")
    admin_users: List[str] = Field(default=[], description="관리자 사용자 목록")
    blocked_keywords: List[str] = Field(default=[], description="금지어 목록")
    
    # Spotify 설정
    spotify: Dict[str, Any] = Field(default_factory=lambda: {
        "enabled": True,
        "client_id": None,
        "client_secret": None
    })
    
    # YouTube 설정  
    youtube: Dict[str, Any] = Field(default_factory=lambda: {
        "enabled": True
    })


class LoggingConfig(BaseModel):
    """로깅 설정"""
    level: str = Field(default="INFO", description="로그 레벨")
    file_logging: bool = Field(default=True, description="파일 로깅 활성화")
    log_dir: str = Field(default="logs", description="로그 디렉토리")
    max_file_size: str = Field(default="10MB", description="최대 로그 파일 크기")
    backup_count: int = Field(default=5, description="백업 파일 개수")


class BotConfig(BaseModel):
    """봇 전체 설정"""
    tiktok: TikTokConfig = Field(default_factory=TikTokConfig)
    features: BotFeatures = Field(default_factory=BotFeatures)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    music: MusicConfig = Field(default_factory=MusicConfig)
    overlay: OverlayConfig = Field(default_factory=OverlayConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # 명령어 설정
    commands: Dict[str, str] = Field(
        default={
            "!help": "사용 가능한 명령어를 확인하세요!",
            "!info": "이 방송은 TikBot으로 자동화되고 있습니다.",
            "!time": "현재 방송 시간을 확인하세요.",
        },
        description="봇 명령어 설정"
    )
    
    # 자동 응답 설정
    auto_responses: Dict[str, List[str]] = Field(
        default={
            "안녕": ["안녕하세요! 👋", "반가워요!", "환영합니다! 🎉"],
            "고마워": ["천만에요! 😊", "도움이 되어서 기뻐요!", "언제든지요! ✨"],
            "bye": ["안녕히 가세요! 👋", "또 봐요!", "수고하셨어요! 🙏"],
        },
        description="키워드별 자동 응답"
    )
    
    # 스팸 필터 설정
    spam_keywords: List[str] = Field(
        default=["스팸", "광고", "홍보"],
        description="스팸으로 간주할 키워드"
    )
    
    @classmethod
    def load_from_file(cls, filepath: Optional[Path] = None) -> "BotConfig":
        """파일에서 설정 로드"""
        if filepath is None:
            filepath = Path("config.yaml")
        
        if not filepath.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return cls(**data)
    
    def save_to_file(self, filepath: Optional[Path] = None):
        """설정을 파일로 저장"""
        if filepath is None:
            filepath = Path("config.yaml")
        
        # 디렉토리 생성
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # YAML로 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(
                self.model_dump(),
                f,
                default_flow_style=False,
                allow_unicode=True,
                indent=2
            )
    
    @classmethod
    def create_default(cls) -> "BotConfig":
        """기본 설정 생성"""
        config = cls()
        config.tiktok.username = "your_tiktok_username"  # 사용자가 변경해야 함
        return config
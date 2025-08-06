"""
Sound Alerts 시스템 - 이벤트별 효과음 관리
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from .player import AudioPlayer
from ..core.events import EventType


class AlertType(Enum):
    """Alert 타입 정의"""
    FOLLOW = "follow"
    GIFT = "gift" 
    COMMENT = "comment"
    LIKE = "like"
    SHARE = "share"
    JOIN = "join"
    COMMAND = "command"
    WELCOME = "welcome"
    MILESTONE = "milestone"


@dataclass
class SoundAlert:
    """사운드 알림 정의"""
    name: str
    file_path: str
    volume: float = 0.7
    cooldown: int = 0  # 쿨다운 (초)
    enabled: bool = True
    conditions: Dict[str, Any] = None  # 조건 (예: 최소 선물 개수)


class SoundAlerts:
    """Sound Alerts 매니저"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.player = AudioPlayer(logger=self.logger)
        
        # 사운드 알림 설정
        self.alerts: Dict[AlertType, List[SoundAlert]] = {}
        self.cooldowns: Dict[str, float] = {}  # 쿨다운 추적
        
        # 기본 사운드 디렉토리
        self.sounds_dir = Path(config.get('sounds_directory', 'static/sounds'))
        self.sounds_dir.mkdir(parents=True, exist_ok=True)
        
        # 통계
        self.stats = {
            "total_alerts": 0,
            "alerts_played": 0,
            "alerts_skipped": 0,
            "cooldown_blocks": 0
        }
        
        self._load_default_alerts()
        self._load_custom_alerts()
    
    def _load_default_alerts(self):
        """기본 알림 설정 로드"""
        default_alerts = {
            AlertType.FOLLOW: [
                SoundAlert(
                    name="새 팔로워",
                    file_path="static/sounds/follow.wav",
                    volume=0.8,
                    cooldown=2
                )
            ],
            AlertType.GIFT: [
                SoundAlert(
                    name="선물 받음",
                    file_path="static/sounds/gift.wav", 
                    volume=0.9,
                    cooldown=1,
                    conditions={"min_count": 1}
                ),
                SoundAlert(
                    name="큰 선물",
                    file_path="static/sounds/big_gift.wav",
                    volume=1.0,
                    cooldown=3,
                    conditions={"min_count": 10}
                )
            ],
            AlertType.COMMENT: [
                SoundAlert(
                    name="새 댓글",
                    file_path="static/sounds/comment.wav",
                    volume=0.5,
                    cooldown=5
                )
            ],
            AlertType.LIKE: [
                SoundAlert(
                    name="좋아요",
                    file_path="static/sounds/like.wav",
                    volume=0.4,
                    cooldown=10
                )
            ],
            AlertType.JOIN: [
                SoundAlert(
                    name="방 입장",
                    file_path="static/sounds/join.wav",
                    volume=0.6,
                    cooldown=30
                )
            ],
            AlertType.COMMAND: [
                SoundAlert(
                    name="명령어 실행",
                    file_path="static/sounds/command.wav",
                    volume=0.5,
                    cooldown=1
                )
            ]
        }
        
        self.alerts.update(default_alerts)
    
    def _load_custom_alerts(self):
        """사용자 정의 알림 로드"""
        custom_config = self.config.get('custom_alerts', {})
        
        for alert_type_name, alert_configs in custom_config.items():
            try:
                alert_type = AlertType(alert_type_name)
                custom_alerts = []
                
                for alert_config in alert_configs:
                    alert = SoundAlert(
                        name=alert_config.get('name', '사용자 정의'),
                        file_path=alert_config.get('file_path', ''),
                        volume=alert_config.get('volume', 0.7),
                        cooldown=alert_config.get('cooldown', 0),
                        enabled=alert_config.get('enabled', True),
                        conditions=alert_config.get('conditions', {})
                    )
                    custom_alerts.append(alert)
                
                # 기존 알림과 병합
                if alert_type in self.alerts:
                    self.alerts[alert_type].extend(custom_alerts)
                else:
                    self.alerts[alert_type] = custom_alerts
                    
            except ValueError:
                self.logger.warning(f"알 수 없는 Alert 타입: {alert_type_name}")
    
    async def trigger_alert(self, event_type: EventType, event_data: Dict[str, Any] = None) -> bool:
        """
        이벤트에 따른 알림 트리거
        
        Args:
            event_type: 이벤트 타입
            event_data: 이벤트 데이터
        
        Returns:
            알림 재생 성공 여부
        """
        if not self.player.is_available():
            return False
        
        # EventType을 AlertType으로 매핑
        alert_type = self._map_event_to_alert(event_type)
        if not alert_type:
            return False
        
        # 해당 타입의 알림들 가져오기
        alerts = self.alerts.get(alert_type, [])
        if not alerts:
            return False
        
        # 조건에 맞는 알림 찾기
        suitable_alert = self._find_suitable_alert(alerts, event_data or {})
        if not suitable_alert:
            self.stats["alerts_skipped"] += 1
            return False
        
        # 쿨다운 체크
        if self._is_in_cooldown(suitable_alert):
            self.stats["cooldown_blocks"] += 1
            return False
        
        # 알림 재생
        success = await self._play_alert(suitable_alert)
        
        if success:
            self.stats["alerts_played"] += 1
            self._set_cooldown(suitable_alert)
        else:
            self.stats["alerts_skipped"] += 1
        
        self.stats["total_alerts"] += 1
        return success
    
    def _map_event_to_alert(self, event_type: EventType) -> Optional[AlertType]:
        """EventType을 AlertType으로 매핑"""
        mapping = {
            EventType.FOLLOW: AlertType.FOLLOW,
            EventType.GIFT: AlertType.GIFT,
            EventType.COMMENT: AlertType.COMMENT,
            EventType.LIKE: AlertType.LIKE,
            EventType.SHARE: AlertType.SHARE,
            EventType.JOIN: AlertType.JOIN,
            EventType.COMMAND: AlertType.COMMAND
        }
        return mapping.get(event_type)
    
    def _find_suitable_alert(self, alerts: List[SoundAlert], event_data: Dict[str, Any]) -> Optional[SoundAlert]:
        """조건에 맞는 알림 찾기"""
        for alert in alerts:
            if not alert.enabled:
                continue
            
            # 파일 존재 확인
            if not Path(alert.file_path).exists():
                continue
            
            # 조건 확인
            if alert.conditions:
                if not self._check_conditions(alert.conditions, event_data):
                    continue
            
            return alert
        
        return None
    
    def _check_conditions(self, conditions: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """알림 조건 확인"""
        # 최소 선물 개수 조건
        if 'min_count' in conditions:
            gift_count = event_data.get('gift_count', 0)
            if gift_count < conditions['min_count']:
                return False
        
        # 최소 코인 가치 조건  
        if 'min_coins' in conditions:
            coins = event_data.get('coins', 0)
            if coins < conditions['min_coins']:
                return False
        
        # VIP 사용자 전용
        if conditions.get('vip_only', False):
            is_vip = event_data.get('is_vip', False)
            if not is_vip:
                return False
        
        return True
    
    def _is_in_cooldown(self, alert: SoundAlert) -> bool:
        """쿨다운 상태 확인"""
        if alert.cooldown <= 0:
            return False
        
        import time
        last_played = self.cooldowns.get(alert.name, 0)
        return (time.time() - last_played) < alert.cooldown
    
    def _set_cooldown(self, alert: SoundAlert):
        """쿨다운 설정"""
        if alert.cooldown > 0:
            import time
            self.cooldowns[alert.name] = time.time()
    
    async def _play_alert(self, alert: SoundAlert) -> bool:
        """알림 재생"""
        try:
            success = await self.player.play_sound(alert.file_path, alert.volume)
            if success:
                self.logger.info(f"🔊 알림 재생: {alert.name}")
            return success
        except Exception as e:
            self.logger.error(f"알림 재생 실패: {e}")
            return False
    
    def add_custom_alert(self, alert_type: AlertType, alert: SoundAlert):
        """사용자 정의 알림 추가"""
        if alert_type not in self.alerts:
            self.alerts[alert_type] = []
        
        self.alerts[alert_type].append(alert)
        self.logger.info(f"사용자 정의 알림 추가: {alert.name}")
    
    def remove_alert(self, alert_type: AlertType, alert_name: str) -> bool:
        """알림 제거"""
        if alert_type not in self.alerts:
            return False
        
        alerts = self.alerts[alert_type]
        for i, alert in enumerate(alerts):
            if alert.name == alert_name:
                del alerts[i]
                self.logger.info(f"알림 제거: {alert_name}")
                return True
        
        return False
    
    def set_alert_enabled(self, alert_type: AlertType, alert_name: str, enabled: bool) -> bool:
        """알림 활성화/비활성화"""
        if alert_type not in self.alerts:
            return False
        
        for alert in self.alerts[alert_type]:
            if alert.name == alert_name:
                alert.enabled = enabled
                status = "활성화" if enabled else "비활성화"
                self.logger.info(f"알림 {status}: {alert_name}")
                return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        stats = self.stats.copy()
        stats.update({
            "available_alerts": sum(len(alerts) for alerts in self.alerts.values()),
            "player_available": self.player.is_available(),
            "current_volume": self.player.get_volume()
        })
        return stats
    
    def set_global_volume(self, volume: float):
        """전역 볼륨 설정"""
        self.player.set_volume(volume)
    
    def stop_all_sounds(self):
        """모든 사운드 중지"""
        self.player.stop_all()
    
    def cleanup(self):
        """리소스 정리"""
        self.player.cleanup()
        self.logger.info("Sound Alerts 시스템 정리 완료")
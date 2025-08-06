"""
음악 큐 관리 시스템
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class RequestStatus(Enum):
    """요청 상태"""
    PENDING = "pending"
    PLAYING = "playing"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class MusicRequest:
    """음악 요청 데이터"""
    id: str
    title: str
    artist: str
    duration: int  # 초
    platform: str  # spotify, youtube
    url: str
    requester: str
    requester_nickname: str
    timestamp: datetime
    status: RequestStatus = RequestStatus.PENDING
    
    # 추가 메타데이터
    album: Optional[str] = None
    thumbnail: Optional[str] = None
    explicit: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['status'] = self.status.value
        return data


class MusicQueue:
    """음악 큐 관리자"""
    
    def __init__(self, max_queue_size: int = 50, max_duration: int = 600,
                 logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.max_queue_size = max_queue_size
        self.max_duration = max_duration  # 최대 곡 길이 (초)
        
        # 큐 관리
        self.queue: List[MusicRequest] = []
        self.history: List[MusicRequest] = []
        self.current_request: Optional[MusicRequest] = None
        
        # 사용자별 제한
        self.user_request_limits = {}  # username -> count
        self.max_requests_per_user = 3
        
        # 통계
        self.stats = {
            "total_requests": 0,
            "completed_songs": 0,
            "skipped_songs": 0,
            "failed_songs": 0,
            "total_duration_played": 0
        }
        
        # 필터링 설정
        self.blocked_keywords = set()
        self.allowed_platforms = {"spotify", "youtube"}
    
    async def add_request(self, request: MusicRequest) -> Dict[str, Any]:
        """큐에 음악 요청 추가"""
        # 유효성 검사
        validation_result = self._validate_request(request)
        if not validation_result["valid"]:
            return validation_result
        
        # 큐 크기 확인
        if len(self.queue) >= self.max_queue_size:
            return {
                "success": False,
                "error": f"큐가 가득 참 (최대 {self.max_queue_size}곡)",
                "queue_size": len(self.queue)
            }
        
        # 사용자별 요청 제한 확인
        user_requests = self.user_request_limits.get(request.requester, 0)
        if user_requests >= self.max_requests_per_user:
            return {
                "success": False,
                "error": f"사용자당 최대 {self.max_requests_per_user}곡까지 요청 가능",
                "user_requests": user_requests
            }
        
        # 큐에 추가
        self.queue.append(request)
        self.user_request_limits[request.requester] = user_requests + 1
        self.stats["total_requests"] += 1
        
        self.logger.info(f"음악 요청 추가: {request.title} by {request.artist} (요청자: {request.requester_nickname})")
        
        return {
            "success": True,
            "message": f"'{request.title}'이(가) 큐에 추가되었습니다",
            "queue_position": len(self.queue),
            "queue_size": len(self.queue),
            "request_id": request.id
        }
    
    def _validate_request(self, request: MusicRequest) -> Dict[str, Any]:
        """요청 유효성 검사"""
        # 곡 길이 확인
        if request.duration > self.max_duration:
            return {
                "valid": False,
                "error": f"곡 길이가 너무 김 (최대 {self.max_duration//60}분)"
            }
        
        # 플랫폼 확인
        if request.platform not in self.allowed_platforms:
            return {
                "valid": False,
                "error": f"지원하지 않는 플랫폼: {request.platform}"
            }
        
        # 금지어 확인
        text_to_check = f"{request.title} {request.artist}".lower()
        for keyword in self.blocked_keywords:
            if keyword.lower() in text_to_check:
                return {
                    "valid": False,
                    "error": "부적절한 내용이 포함된 요청"
                }
        
        # 중복 확인 (큐 내)
        for existing in self.queue:
            if (existing.title.lower() == request.title.lower() and 
                existing.artist.lower() == request.artist.lower()):
                return {
                    "valid": False,
                    "error": "이미 큐에 있는 곡입니다"
                }
        
        return {"valid": True}
    
    async def get_next_request(self) -> Optional[MusicRequest]:
        """다음 재생할 곡 가져오기"""
        if not self.queue:
            return None
        
        # 현재 재생 중인 곡을 히스토리로 이동
        if self.current_request:
            self.current_request.status = RequestStatus.COMPLETED
            self.history.append(self.current_request)
            self.stats["completed_songs"] += 1
            self.stats["total_duration_played"] += self.current_request.duration
            
            # 사용자 요청 카운터 감소
            if self.current_request.requester in self.user_request_limits:
                self.user_request_limits[self.current_request.requester] -= 1
        
        # 다음 곡을 현재 재생으로 설정
        self.current_request = self.queue.pop(0)
        self.current_request.status = RequestStatus.PLAYING
        
        self.logger.info(f"다음 곡 재생: {self.current_request.title}")
        return self.current_request
    
    async def skip_current(self, reason: str = "사용자 요청") -> bool:
        """현재 곡 스킵"""
        if not self.current_request:
            return False
        
        self.current_request.status = RequestStatus.SKIPPED
        self.history.append(self.current_request)
        self.stats["skipped_songs"] += 1
        
        # 사용자 요청 카운터 감소
        if self.current_request.requester in self.user_request_limits:
            self.user_request_limits[self.current_request.requester] -= 1
        
        self.logger.info(f"곡 스킵: {self.current_request.title} (이유: {reason})")
        self.current_request = None
        
        return True
    
    async def remove_request(self, request_id: str, requester: str = None) -> bool:
        """큐에서 요청 제거"""
        for i, request in enumerate(self.queue):
            if request.id == request_id:
                # 요청자 본인만 제거 가능 (관리자는 예외)
                if requester and request.requester != requester:
                    return False
                
                removed_request = self.queue.pop(i)
                
                # 사용자 요청 카운터 감소
                if removed_request.requester in self.user_request_limits:
                    self.user_request_limits[removed_request.requester] -= 1
                
                self.logger.info(f"요청 제거: {removed_request.title}")
                return True
        
        return False
    
    def get_queue_info(self) -> Dict[str, Any]:
        """큐 정보 반환"""
        total_duration = sum(req.duration for req in self.queue)
        
        return {
            "current": self.current_request.to_dict() if self.current_request else None,
            "queue": [req.to_dict() for req in self.queue],
            "queue_size": len(self.queue),
            "total_duration": total_duration,
            "estimated_wait_time": total_duration + (self.current_request.duration if self.current_request else 0),
            "max_queue_size": self.max_queue_size
        }
    
    def get_user_requests(self, username: str) -> List[Dict[str, Any]]:
        """특정 사용자의 요청 목록"""
        user_requests = []
        
        # 현재 재생 중인 곡
        if self.current_request and self.current_request.requester == username:
            user_requests.append(self.current_request.to_dict())
        
        # 큐에 있는 곡들
        for request in self.queue:
            if request.requester == username:
                user_requests.append(request.to_dict())
        
        return user_requests
    
    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """재생 히스토리 반환"""
        return [req.to_dict() for req in self.history[-limit:]]
    
    def clear_queue(self, admin: bool = False) -> bool:
        """큐 비우기 (관리자만)"""
        if not admin:
            return False
        
        self.queue.clear()
        self.user_request_limits.clear()
        self.logger.info("음악 큐가 비워졌습니다")
        return True
    
    def update_settings(self, settings: Dict[str, Any]):
        """설정 업데이트"""
        if "max_queue_size" in settings:
            self.max_queue_size = settings["max_queue_size"]
        
        if "max_duration" in settings:
            self.max_duration = settings["max_duration"]
        
        if "max_requests_per_user" in settings:
            self.max_requests_per_user = settings["max_requests_per_user"]
        
        if "blocked_keywords" in settings:
            self.blocked_keywords = set(settings["blocked_keywords"])
        
        if "allowed_platforms" in settings:
            self.allowed_platforms = set(settings["allowed_platforms"])
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        return {
            **self.stats,
            "queue_size": len(self.queue),
            "history_size": len(self.history),
            "active_users": len([k for k, v in self.user_request_limits.items() if v > 0]),
            "average_song_duration": (
                self.stats["total_duration_played"] // max(1, self.stats["completed_songs"])
            )
        }
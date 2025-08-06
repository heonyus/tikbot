"""
대화 컨텍스트 관리
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum


class MessageType(Enum):
    """메시지 타입"""
    USER_COMMENT = "user_comment"
    BOT_RESPONSE = "bot_response"
    AUTO_RESPONSE = "auto_response"
    SYSTEM_MESSAGE = "system_message"
    AI_SUGGESTION = "ai_suggestion"


@dataclass
class ConversationMessage:
    """대화 메시지"""
    id: str
    type: MessageType
    content: str
    username: str
    nickname: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "username": self.username,
            "nickname": self.nickname,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """딕셔너리에서 생성"""
        return cls(
            id=data["id"],
            type=MessageType(data["type"]),
            content=data["content"],
            username=data["username"],
            nickname=data["nickname"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class UserProfile:
    """사용자 프로필"""
    username: str
    nickname: str
    first_seen: datetime
    last_seen: datetime
    message_count: int = 0
    total_gifts: int = 0
    is_follower: bool = False
    is_vip: bool = False
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "username": self.username,
            "nickname": self.nickname,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "message_count": self.message_count,
            "total_gifts": self.total_gifts,
            "is_follower": self.is_follower,
            "is_vip": self.is_vip,
            "preferences": self.preferences
        }


class ConversationContext:
    """대화 컨텍스트 관리자"""
    
    def __init__(self, max_history: int = 100, context_window: int = 10,
                 logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.max_history = max_history
        self.context_window = context_window
        
        # 대화 히스토리
        self.messages: List[ConversationMessage] = []
        
        # 사용자 프로필
        self.user_profiles: Dict[str, UserProfile] = {}
        
        # 현재 방송 컨텍스트
        self.stream_context = {
            "start_time": datetime.now(),
            "viewer_count": 0,
            "total_messages": 0,
            "total_gifts": 0,
            "total_followers": 0,
            "active_topics": [],
            "mood": "neutral",  # positive, neutral, negative
            "energy_level": "medium"  # low, medium, high
        }
        
        # AI 학습 데이터
        self.learning_data = {
            "popular_topics": {},
            "response_effectiveness": {},
            "user_engagement_patterns": {},
            "peak_activity_times": []
        }
    
    def add_message(self, message: ConversationMessage):
        """메시지 추가"""
        self.messages.append(message)
        
        # 히스토리 크기 제한
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        
        # 사용자 프로필 업데이트
        self._update_user_profile(message)
        
        # 스트림 컨텍스트 업데이트
        self._update_stream_context(message)
        
        # 학습 데이터 업데이트
        self._update_learning_data(message)
    
    def _update_user_profile(self, message: ConversationMessage):
        """사용자 프로필 업데이트"""
        username = message.username
        
        if username not in self.user_profiles:
            self.user_profiles[username] = UserProfile(
                username=username,
                nickname=message.nickname,
                first_seen=message.timestamp,
                last_seen=message.timestamp
            )
        
        profile = self.user_profiles[username]
        profile.last_seen = message.timestamp
        profile.nickname = message.nickname  # 최신 닉네임으로 업데이트
        
        if message.type == MessageType.USER_COMMENT:
            profile.message_count += 1
        
        # 메타데이터에서 추가 정보 추출
        if "gift_count" in message.metadata:
            profile.total_gifts += message.metadata["gift_count"]
        
        if "is_follower" in message.metadata:
            profile.is_follower = message.metadata["is_follower"]
        
        if "is_vip" in message.metadata:
            profile.is_vip = message.metadata["is_vip"]
    
    def _update_stream_context(self, message: ConversationMessage):
        """스트림 컨텍스트 업데이트"""
        if message.type == MessageType.USER_COMMENT:
            self.stream_context["total_messages"] += 1
        
        # 현재 시청자 수 업데이트 (활성 사용자 기준)
        recent_threshold = datetime.now() - timedelta(minutes=5)
        active_users = set()
        
        for msg in reversed(self.messages):
            if msg.timestamp < recent_threshold:
                break
            if msg.type == MessageType.USER_COMMENT:
                active_users.add(msg.username)
        
        self.stream_context["viewer_count"] = len(active_users)
        
        # 활성 토픽 분석
        self._analyze_active_topics()
        
        # 분위기 분석
        self._analyze_mood()
    
    def _analyze_active_topics(self):
        """활성 토픽 분석"""
        recent_messages = [msg for msg in self.messages[-20:] 
                          if msg.type == MessageType.USER_COMMENT]
        
        # 키워드 빈도 분석 (간단한 버전)
        keywords = {}
        for msg in recent_messages:
            words = msg.content.lower().split()
            for word in words:
                if len(word) > 2:  # 3글자 이상만
                    keywords[word] = keywords.get(word, 0) + 1
        
        # 상위 5개 키워드를 활성 토픽으로 설정
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        self.stream_context["active_topics"] = [kw[0] for kw in sorted_keywords[:5]]
    
    def _analyze_mood(self):
        """분위기 분석"""
        recent_messages = [msg for msg in self.messages[-10:] 
                          if msg.type == MessageType.USER_COMMENT]
        
        if not recent_messages:
            return
        
        # 간단한 감정 분석 (키워드 기반)
        positive_words = ["좋아", "최고", "대박", "짱", "사랑", "감사", "행복", "웃음", "재미"]
        negative_words = ["싫어", "별로", "지루", "아쉬", "실망", "화나", "짜증"]
        
        positive_count = 0
        negative_count = 0
        
        for msg in recent_messages:
            content = msg.content.lower()
            for word in positive_words:
                if word in content:
                    positive_count += 1
            for word in negative_words:
                if word in content:
                    negative_count += 1
        
        if positive_count > negative_count * 2:
            self.stream_context["mood"] = "positive"
        elif negative_count > positive_count * 2:
            self.stream_context["mood"] = "negative"
        else:
            self.stream_context["mood"] = "neutral"
        
        # 에너지 레벨 (메시지 빈도 기반)
        message_rate = len(recent_messages) / 10  # 최근 10개 메시지 기준
        if message_rate > 0.8:
            self.stream_context["energy_level"] = "high"
        elif message_rate > 0.3:
            self.stream_context["energy_level"] = "medium"
        else:
            self.stream_context["energy_level"] = "low"
    
    def _update_learning_data(self, message: ConversationMessage):
        """학습 데이터 업데이트"""
        # 인기 토픽 추적
        if message.type == MessageType.USER_COMMENT:
            words = message.content.lower().split()
            for word in words:
                if len(word) > 2:
                    self.learning_data["popular_topics"][word] = \
                        self.learning_data["popular_topics"].get(word, 0) + 1
        
        # 시간대별 활동 패턴
        hour = message.timestamp.hour
        if hour not in [entry["hour"] for entry in self.learning_data["peak_activity_times"]]:
            self.learning_data["peak_activity_times"].append({
                "hour": hour,
                "message_count": 1
            })
        else:
            for entry in self.learning_data["peak_activity_times"]:
                if entry["hour"] == hour:
                    entry["message_count"] += 1
                    break
    
    def get_recent_context(self) -> List[Dict[str, Any]]:
        """최근 컨텍스트 가져오기"""
        recent_messages = self.messages[-self.context_window:]
        return [msg.to_dict() for msg in recent_messages]
    
    def get_user_context(self, username: str) -> Optional[Dict[str, Any]]:
        """특정 사용자 컨텍스트"""
        if username not in self.user_profiles:
            return None
        
        profile = self.user_profiles[username]
        
        # 해당 사용자의 최근 메시지들
        user_messages = [msg for msg in self.messages 
                        if msg.username == username][-5:]  # 최근 5개
        
        return {
            "profile": profile.to_dict(),
            "recent_messages": [msg.to_dict() for msg in user_messages],
            "engagement_level": self._calculate_engagement_level(profile),
            "interaction_style": self._analyze_interaction_style(user_messages)
        }
    
    def _calculate_engagement_level(self, profile: UserProfile) -> str:
        """사용자 참여도 계산"""
        # 메시지 수, 선물, 팔로우 여부 등을 종합
        score = 0
        
        if profile.message_count > 10:
            score += 3
        elif profile.message_count > 5:
            score += 2
        elif profile.message_count > 0:
            score += 1
        
        if profile.total_gifts > 5:
            score += 3
        elif profile.total_gifts > 0:
            score += 1
        
        if profile.is_follower:
            score += 2
        
        if profile.is_vip:
            score += 2
        
        if score >= 8:
            return "high"
        elif score >= 4:
            return "medium"
        else:
            return "low"
    
    def _analyze_interaction_style(self, messages: List[ConversationMessage]) -> str:
        """상호작용 스타일 분석"""
        if not messages:
            return "unknown"
        
        # 메시지 길이 분석
        avg_length = sum(len(msg.content) for msg in messages) / len(messages)
        
        # 이모지 사용 빈도
        emoji_count = sum(1 for msg in messages for char in msg.content 
                         if ord(char) > 0x1F600)
        
        # 질문 빈도
        question_count = sum(1 for msg in messages if '?' in msg.content or '물어' in msg.content)
        
        if avg_length > 20 and question_count > 0:
            return "conversational"
        elif emoji_count > len(messages):
            return "expressive"
        elif avg_length < 10:
            return "brief"
        else:
            return "casual"
    
    def get_stream_insights(self) -> Dict[str, Any]:
        """방송 인사이트 제공"""
        # 활성 사용자 분석
        active_users = len(set(msg.username for msg in self.messages[-20:] 
                              if msg.type == MessageType.USER_COMMENT))
        
        # 참여도 높은 사용자
        engaged_users = [username for username, profile in self.user_profiles.items()
                        if self._calculate_engagement_level(profile) == "high"]
        
        # 인기 토픽
        sorted_topics = sorted(self.learning_data["popular_topics"].items(), 
                             key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "stream_context": self.stream_context,
            "active_users": active_users,
            "engaged_users": engaged_users[:10],  # 상위 10명
            "popular_topics": sorted_topics,
            "total_users": len(self.user_profiles),
            "average_messages_per_user": (
                sum(p.message_count for p in self.user_profiles.values()) / 
                max(1, len(self.user_profiles))
            )
        }
    
    def export_learning_data(self) -> Dict[str, Any]:
        """학습 데이터 내보내기"""
        return {
            "learning_data": self.learning_data,
            "user_profiles": {k: v.to_dict() for k, v in self.user_profiles.items()},
            "stream_insights": self.get_stream_insights(),
            "export_timestamp": datetime.now().isoformat()
        }
    
    def clear_old_data(self, days: int = 7):
        """오래된 데이터 정리"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 오래된 메시지 제거
        self.messages = [msg for msg in self.messages if msg.timestamp > cutoff_date]
        
        # 비활성 사용자 제거
        active_users = set(msg.username for msg in self.messages)
        self.user_profiles = {k: v for k, v in self.user_profiles.items() 
                             if k in active_users}
        
        self.logger.info(f"오래된 데이터 정리 완료: {cutoff_date} 이전 데이터 제거")
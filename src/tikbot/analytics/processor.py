"""
데이터 처리기 - 수집된 데이터 분석 및 인사이트 생성
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics
import json

from .collector import StreamEvent, EventType, StreamSession


@dataclass
class AnalyticsInsight:
    """분석 인사이트"""
    type: str
    title: str
    description: str
    value: Any
    trend: str  # "up", "down", "stable"
    confidence: float  # 0.0 - 1.0
    timestamp: datetime
    metadata: Dict[str, Any]


class DataProcessor:
    """데이터 분석 및 처리기"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # 캐시된 분석 결과
        self._analysis_cache = {}
        self._cache_expiry = {}
        self.cache_duration = 300  # 5분 캐시
    
    async def analyze_engagement(self, events: List[StreamEvent], 
                               time_window: int = 3600) -> Dict[str, Any]:
        """참여도 분석"""
        cache_key = f"engagement_{len(events)}_{time_window}"
        
        if self._is_cache_valid(cache_key):
            return self._analysis_cache[cache_key]
        
        try:
            now = datetime.now()
            recent_events = [
                e for e in events 
                if (now - e.timestamp).total_seconds() <= time_window
            ]
            
            if not recent_events:
                return {"error": "No recent events found"}
            
            # 기본 메트릭
            total_events = len(recent_events)
            unique_users = len(set(e.username for e in recent_events))
            
            # 이벤트 타입별 분석
            event_breakdown = {}
            for event in recent_events:
                event_type = event.event_type.value
                event_breakdown[event_type] = event_breakdown.get(event_type, 0) + 1
            
            # 참여율 계산
            engagement_events = [EventType.COMMENT, EventType.GIFT, EventType.FOLLOW, EventType.LIKE]
            engagement_count = sum(
                event_breakdown.get(et.value, 0) for et in engagement_events
            )
            engagement_rate = engagement_count / max(total_events, 1)
            
            # 시간대별 활동
            hourly_activity = {}
            for event in recent_events:
                hour = event.timestamp.hour
                hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
            
            # 평균 활동 간격
            timestamps = sorted([e.timestamp for e in recent_events])
            intervals = []
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                intervals.append(interval)
            
            avg_interval = statistics.mean(intervals) if intervals else 0
            
            # 활성 사용자 분석
            user_activity = {}
            for event in recent_events:
                username = event.username
                user_activity[username] = user_activity.get(username, 0) + 1
            
            # 상위 활성 사용자
            top_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # 참여도 점수 (0-100)
            engagement_score = min(100, (
                (engagement_rate * 40) +
                (min(unique_users / 10, 1) * 30) +
                (min(len(top_users) / 5, 1) * 20) +
                (min(60 / max(avg_interval, 1), 1) * 10)
            ))
            
            result = {
                "total_events": total_events,
                "unique_users": unique_users,
                "engagement_rate": engagement_rate,
                "engagement_score": engagement_score,
                "event_breakdown": event_breakdown,
                "hourly_activity": hourly_activity,
                "avg_interval_seconds": avg_interval,
                "top_users": [{"username": u, "activity": a} for u, a in top_users],
                "analysis_timestamp": now.isoformat()
            }
            
            self._cache_result(cache_key, result)
            return result
            
        except Exception as e:
            self.logger.error(f"참여도 분석 실패: {e}")
            return {"error": str(e)}
    
    async def analyze_growth_trends(self, events: List[StreamEvent],
                                   days: int = 7) -> Dict[str, Any]:
        """성장 트렌드 분석"""
        cache_key = f"growth_{len(events)}_{days}"
        
        if self._is_cache_valid(cache_key):
            return self._analysis_cache[cache_key]
        
        try:
            now = datetime.now()
            cutoff_date = now - timedelta(days=days)
            
            # 기간별 데이터 분리
            recent_events = [e for e in events if e.timestamp >= cutoff_date]
            
            if not recent_events:
                return {"error": "Insufficient data for trend analysis"}
            
            # 일별 활동 분석
            daily_stats = {}
            for event in recent_events:
                date_key = event.timestamp.date().isoformat()
                
                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        "total_events": 0,
                        "unique_users": set(),
                        "comments": 0,
                        "gifts": 0,
                        "follows": 0,
                        "likes": 0
                    }
                
                daily_stats[date_key]["total_events"] += 1
                daily_stats[date_key]["unique_users"].add(event.username)
                
                if event.event_type == EventType.COMMENT:
                    daily_stats[date_key]["comments"] += 1
                elif event.event_type == EventType.GIFT:
                    daily_stats[date_key]["gifts"] += 1
                elif event.event_type == EventType.FOLLOW:
                    daily_stats[date_key]["follows"] += 1
                elif event.event_type == EventType.LIKE:
                    daily_stats[date_key]["likes"] += 1
            
            # 고유 사용자 수를 정수로 변환
            for date_key in daily_stats:
                daily_stats[date_key]["unique_users"] = len(daily_stats[date_key]["unique_users"])
            
            # 트렌드 계산
            dates = sorted(daily_stats.keys())
            metrics = ["total_events", "unique_users", "comments", "gifts", "follows", "likes"]
            
            trends = {}
            for metric in metrics:
                values = [daily_stats[date][metric] for date in dates]
                
                if len(values) >= 2:
                    # 선형 회귀를 통한 트렌드 계산
                    trend_slope = self._calculate_trend_slope(values)
                    
                    trends[metric] = {
                        "values": values,
                        "slope": trend_slope,
                        "trend": "up" if trend_slope > 0.1 else "down" if trend_slope < -0.1 else "stable",
                        "growth_rate": (values[-1] - values[0]) / max(values[0], 1) * 100 if values[0] > 0 else 0
                    }
                else:
                    trends[metric] = {
                        "values": values,
                        "slope": 0,
                        "trend": "stable",
                        "growth_rate": 0
                    }
            
            # 종합 성장 점수
            growth_score = 0
            for metric in ["unique_users", "comments", "gifts", "follows"]:
                if metric in trends:
                    growth_rate = trends[metric]["growth_rate"]
                    growth_score += max(0, min(25, growth_rate))  # 각 메트릭 최대 25점
            
            result = {
                "analysis_period_days": days,
                "daily_stats": daily_stats,
                "trends": trends,
                "growth_score": growth_score,
                "dates": dates,
                "analysis_timestamp": now.isoformat()
            }
            
            self._cache_result(cache_key, result)
            return result
            
        except Exception as e:
            self.logger.error(f"성장 트렌드 분석 실패: {e}")
            return {"error": str(e)}
    
    async def analyze_user_behavior(self, events: List[StreamEvent]) -> Dict[str, Any]:
        """사용자 행동 분석"""
        cache_key = f"user_behavior_{len(events)}"
        
        if self._is_cache_valid(cache_key):
            return self._analysis_cache[cache_key]
        
        try:
            # 사용자별 활동 프로필
            user_profiles = {}
            
            for event in events:
                username = event.username
                
                if username not in user_profiles:
                    user_profiles[username] = {
                        "nickname": event.nickname,
                        "first_seen": event.timestamp,
                        "last_seen": event.timestamp,
                        "total_events": 0,
                        "event_types": {},
                        "session_count": 0,
                        "avg_session_length": 0,
                        "engagement_level": "low"
                    }
                
                profile = user_profiles[username]
                profile["total_events"] += 1
                profile["last_seen"] = max(profile["last_seen"], event.timestamp)
                profile["first_seen"] = min(profile["first_seen"], event.timestamp)
                
                event_type = event.event_type.value
                profile["event_types"][event_type] = profile["event_types"].get(event_type, 0) + 1
            
            # 사용자 분류 및 점수 계산
            for username, profile in user_profiles.items():
                # 활동 기간
                activity_span = (profile["last_seen"] - profile["first_seen"]).total_seconds()
                
                # 참여도 점수
                engagement_score = 0
                
                # 이벤트 다양성
                event_diversity = len(profile["event_types"])
                engagement_score += event_diversity * 5
                
                # 총 활동량
                engagement_score += min(profile["total_events"], 50)
                
                # 고가치 이벤트 (선물, 팔로우)
                high_value_events = (
                    profile["event_types"].get("gift", 0) * 10 +
                    profile["event_types"].get("follow", 0) * 5
                )
                engagement_score += high_value_events
                
                # 참여도 레벨 결정
                if engagement_score >= 100:
                    profile["engagement_level"] = "high"
                elif engagement_score >= 30:
                    profile["engagement_level"] = "medium"
                else:
                    profile["engagement_level"] = "low"
                
                profile["engagement_score"] = engagement_score
                profile["activity_span_hours"] = activity_span / 3600
            
            # 통계 계산
            total_users = len(user_profiles)
            engagement_distribution = {"high": 0, "medium": 0, "low": 0}
            
            for profile in user_profiles.values():
                engagement_distribution[profile["engagement_level"]] += 1
            
            # 상위 사용자
            top_users = sorted(
                user_profiles.items(),
                key=lambda x: x[1]["engagement_score"],
                reverse=True
            )[:20]
            
            # 사용자 리텐션 분석
            now = datetime.now()
            retention_periods = [1, 7, 30]  # days
            retention_stats = {}
            
            for period in retention_periods:
                cutoff_date = now - timedelta(days=period)
                active_users = sum(
                    1 for profile in user_profiles.values()
                    if profile["last_seen"] >= cutoff_date
                )
                retention_stats[f"{period}d"] = {
                    "active_users": active_users,
                    "retention_rate": active_users / max(total_users, 1)
                }
            
            result = {
                "total_users": total_users,
                "engagement_distribution": engagement_distribution,
                "top_users": [
                    {
                        "username": username,
                        "nickname": profile["nickname"],
                        "engagement_score": profile["engagement_score"],
                        "engagement_level": profile["engagement_level"],
                        "total_events": profile["total_events"],
                        "event_types": profile["event_types"]
                    }
                    for username, profile in top_users
                ],
                "retention_stats": retention_stats,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            self._cache_result(cache_key, result)
            return result
            
        except Exception as e:
            self.logger.error(f"사용자 행동 분석 실패: {e}")
            return {"error": str(e)}
    
    async def generate_insights(self, events: List[StreamEvent]) -> List[AnalyticsInsight]:
        """인사이트 생성"""
        insights = []
        
        try:
            # 참여도 분석
            engagement_data = await self.analyze_engagement(events)
            if "error" not in engagement_data:
                insights.extend(self._extract_engagement_insights(engagement_data))
            
            # 성장 트렌드 분석
            growth_data = await self.analyze_growth_trends(events)
            if "error" not in growth_data:
                insights.extend(self._extract_growth_insights(growth_data))
            
            # 사용자 행동 분석
            behavior_data = await self.analyze_user_behavior(events)
            if "error" not in behavior_data:
                insights.extend(self._extract_behavior_insights(behavior_data))
            
        except Exception as e:
            self.logger.error(f"인사이트 생성 실패: {e}")
        
        return insights
    
    def _extract_engagement_insights(self, data: Dict[str, Any]) -> List[AnalyticsInsight]:
        """참여도 인사이트 추출"""
        insights = []
        
        # 참여도 점수 인사이트
        score = data.get("engagement_score", 0)
        if score >= 80:
            trend = "up"
            description = "시청자들의 참여도가 매우 높습니다!"
        elif score >= 50:
            trend = "stable"
            description = "적당한 수준의 참여도를 보이고 있습니다."
        else:
            trend = "down"
            description = "참여도 향상이 필요합니다."
        
        insights.append(AnalyticsInsight(
            type="engagement",
            title="시청자 참여도",
            description=description,
            value=score,
            trend=trend,
            confidence=0.8,
            timestamp=datetime.now(),
            metadata={"threshold_high": 80, "threshold_medium": 50}
        ))
        
        # 고유 사용자 인사이트
        unique_users = data.get("unique_users", 0)
        if unique_users >= 20:
            insights.append(AnalyticsInsight(
                type="audience",
                title="활성 시청자",
                description=f"{unique_users}명의 활성 시청자가 참여하고 있습니다.",
                value=unique_users,
                trend="up",
                confidence=0.9,
                timestamp=datetime.now(),
                metadata={}
            ))
        
        return insights
    
    def _extract_growth_insights(self, data: Dict[str, Any]) -> List[AnalyticsInsight]:
        """성장 트렌드 인사이트 추출"""
        insights = []
        
        trends = data.get("trends", {})
        
        # 팔로워 성장
        if "follows" in trends:
            follow_data = trends["follows"]
            growth_rate = follow_data.get("growth_rate", 0)
            
            if growth_rate > 20:
                insights.append(AnalyticsInsight(
                    type="growth",
                    title="팔로워 급증",
                    description=f"팔로워가 {growth_rate:.1f}% 증가했습니다!",
                    value=growth_rate,
                    trend="up",
                    confidence=0.9,
                    timestamp=datetime.now(),
                    metadata={"metric": "follows"}
                ))
            elif growth_rate < -10:
                insights.append(AnalyticsInsight(
                    type="growth",
                    title="팔로워 감소",
                    description=f"팔로워가 {abs(growth_rate):.1f}% 감소했습니다.",
                    value=growth_rate,
                    trend="down",
                    confidence=0.8,
                    timestamp=datetime.now(),
                    metadata={"metric": "follows"}
                ))
        
        return insights
    
    def _extract_behavior_insights(self, data: Dict[str, Any]) -> List[AnalyticsInsight]:
        """사용자 행동 인사이트 추출"""
        insights = []
        
        engagement_dist = data.get("engagement_distribution", {})
        total_users = data.get("total_users", 0)
        
        if total_users > 0:
            high_engagement_ratio = engagement_dist.get("high", 0) / total_users
            
            if high_engagement_ratio > 0.3:
                insights.append(AnalyticsInsight(
                    type="audience_quality",
                    title="고참여 시청자 비율 높음",
                    description=f"시청자의 {high_engagement_ratio*100:.1f}%가 높은 참여도를 보입니다.",
                    value=high_engagement_ratio,
                    trend="up",
                    confidence=0.8,
                    timestamp=datetime.now(),
                    metadata={}
                ))
        
        return insights
    
    def _calculate_trend_slope(self, values: List[float]) -> float:
        """트렌드 기울기 계산 (단순 선형 회귀)"""
        if len(values) < 2:
            return 0
        
        n = len(values)
        x_values = list(range(n))
        
        # 평균 계산
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        # 기울기 계산
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
        
        return numerator / denominator
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """캐시 유효성 확인"""
        if cache_key not in self._analysis_cache:
            return False
        
        if cache_key not in self._cache_expiry:
            return False
        
        return datetime.now() < self._cache_expiry[cache_key]
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """결과 캐싱"""
        self._analysis_cache[cache_key] = result
        self._cache_expiry[cache_key] = datetime.now() + timedelta(seconds=self.cache_duration)
    
    def clear_cache(self):
        """캐시 클리어"""
        self._analysis_cache.clear()
        self._cache_expiry.clear()
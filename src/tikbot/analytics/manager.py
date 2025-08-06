"""
Analytics Manager - 데이터 수집, 분석, 시각화 통합 관리
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .collector import DataCollector, EventType as AnalyticsEventType
from .processor import DataProcessor
from .visualizer import DataVisualizer
from ..core.events import EventHandler, EventType


class AnalyticsManager:
    """통합 분석 매니저"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.enabled = config.get('enabled', True)
        
        # 컴포넌트들
        self.collector: Optional[DataCollector] = None
        self.processor: Optional[DataProcessor] = None
        self.visualizer: Optional[DataVisualizer] = None
        
        # 설정
        self.auto_session_start = config.get('auto_session_start', True)
        self.real_time_analysis = config.get('real_time_analysis', True)
        self.chart_format = config.get('chart_format', 'plotly')
        self.theme = config.get('theme', 'dark')
        
        # 캐시된 분석 결과
        self._cached_dashboard = None
        self._cache_timestamp = None
        self.cache_duration = 60  # 1분 캐시
        
        # 통계
        self.stats = {
            "initialization_time": None,
            "events_processed": 0,
            "analyses_performed": 0,
            "charts_generated": 0,
            "cache_hits": 0
        }
    
    async def initialize(self) -> bool:
        """분석 시스템 초기화"""
        if not self.enabled:
            self.logger.info("분석 시스템이 비활성화되어 있습니다.")
            return True
        
        try:
            import time
            start_time = time.time()
            
            # 데이터 수집기 초기화
            collector_config = self.config.get('collector', {})
            self.collector = DataCollector(
                data_dir=collector_config.get('data_dir', 'data'),
                buffer_size=collector_config.get('buffer_size', 100),
                flush_interval=collector_config.get('flush_interval', 60),
                logger=self.logger
            )
            
            if not await self.collector.initialize():
                self.logger.error("데이터 수집기 초기화 실패")
                return False
            
            # 데이터 처리기 초기화
            self.processor = DataProcessor(logger=self.logger)
            
            # 시각화 생성기 초기화
            self.visualizer = DataVisualizer(
                theme=self.theme,
                logger=self.logger
            )
            
            # 자동 세션 시작
            if self.auto_session_start:
                await self.collector.start_session(
                    title=f"TikBot Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    category="live_stream"
                )
            
            # 초기화 시간 기록
            self.stats["initialization_time"] = time.time() - start_time
            
            self.logger.info(f"📊 분석 시스템 초기화 완료 - 차트 형식: {self.chart_format}")
            return True
            
        except Exception as e:
            self.logger.error(f"분석 시스템 초기화 실패: {e}")
            return False
    
    def register_event_handlers(self, event_handler: EventHandler):
        """이벤트 핸들러에 분석 이벤트 등록"""
        if not self.enabled or not self.collector:
            return
        
        @event_handler.on(EventType.COMMENT)
        async def on_comment_analytics(event_data):
            await self.collector.collect_event(
                AnalyticsEventType.COMMENT,
                event_data.get("username", ""),
                event_data.get("nickname", ""),
                event_data
            )
            self.stats["events_processed"] += 1
            await self._invalidate_cache()
        
        @event_handler.on(EventType.GIFT)
        async def on_gift_analytics(event_data):
            await self.collector.collect_event(
                AnalyticsEventType.GIFT,
                event_data.get("username", ""),
                event_data.get("nickname", ""),
                event_data
            )
            self.stats["events_processed"] += 1
            await self._invalidate_cache()
        
        @event_handler.on(EventType.FOLLOW)
        async def on_follow_analytics(event_data):
            await self.collector.collect_event(
                AnalyticsEventType.FOLLOW,
                event_data.get("username", ""),
                event_data.get("nickname", ""),
                event_data
            )
            self.stats["events_processed"] += 1
            await self._invalidate_cache()
        
        @event_handler.on(EventType.LIKE)
        async def on_like_analytics(event_data):
            await self.collector.collect_event(
                AnalyticsEventType.LIKE,
                event_data.get("username", ""),
                event_data.get("nickname", ""),
                event_data
            )
            self.stats["events_processed"] += 1
            await self._invalidate_cache()
        
        @event_handler.on(EventType.JOIN)
        async def on_join_analytics(event_data):
            await self.collector.collect_event(
                AnalyticsEventType.JOIN,
                event_data.get("username", ""),
                event_data.get("nickname", ""),
                event_data
            )
            self.stats["events_processed"] += 1
            await self._invalidate_cache()
        
        # 봇 응답 이벤트
        @event_handler.on(EventType.AUTO_RESPONSE)
        async def on_bot_response_analytics(event_data):
            await self.collector.collect_event(
                AnalyticsEventType.BOT_RESPONSE,
                "tikbot",
                "TikBot",
                event_data
            )
            self.stats["events_processed"] += 1
        
        # 음악 요청 이벤트
        @event_handler.on(EventType.MUSIC_REQUEST_ADDED)
        async def on_music_request_analytics(event_data):
            await self.collector.collect_event(
                AnalyticsEventType.MUSIC_REQUEST,
                event_data.get("requester", ""),
                event_data.get("requester_nickname", ""),
                event_data
            )
            self.stats["events_processed"] += 1
        
        # AI 상호작용 이벤트
        @event_handler.on(EventType.COMMAND)
        async def on_ai_interaction_analytics(event_data):
            command = event_data.get("command", "")
            if command.startswith("!ai"):
                await self.collector.collect_event(
                    AnalyticsEventType.AI_INTERACTION,
                    event_data.get("username", ""),
                    event_data.get("nickname", ""),
                    event_data
                )
                self.stats["events_processed"] += 1
        
        self.logger.info("분석 이벤트 핸들러 등록 완료")
    
    async def get_realtime_dashboard(self) -> Dict[str, Any]:
        """실시간 대시보드 데이터"""
        # 캐시 확인
        if self._is_cache_valid():
            self.stats["cache_hits"] += 1
            return self._cached_dashboard
        
        try:
            if not self.collector or not self.processor:
                return {"error": "분석 시스템이 초기화되지 않았습니다"}
            
            # 최근 이벤트 가져오기 (최근 1시간)
            recent_events = await self.collector.get_events(
                start_time=datetime.now() - timedelta(hours=1),
                limit=5000
            )
            
            if not recent_events:
                return {
                    "message": "분석할 데이터가 없습니다",
                    "realtime_stats": self.collector.get_realtime_stats()
                }
            
            # 분석 수행
            engagement_data = await self.processor.analyze_engagement(recent_events)
            growth_data = await self.processor.analyze_growth_trends(recent_events)
            behavior_data = await self.processor.analyze_user_behavior(recent_events)
            
            self.stats["analyses_performed"] += 3
            
            # 시각화 생성 (선택적)
            charts = {}
            if self.visualizer:
                try:
                    charts["engagement"] = await self.visualizer.create_engagement_chart(
                        engagement_data, self.chart_format
                    )
                    charts["trends"] = await self.visualizer.create_trend_chart(
                        growth_data, self.chart_format
                    )
                    charts["users"] = await self.visualizer.create_user_distribution_chart(
                        behavior_data, self.chart_format
                    )
                    
                    self.stats["charts_generated"] += 3
                    
                except Exception as e:
                    self.logger.warning(f"차트 생성 중 일부 오류: {e}")
            
            # 대시보드 요약
            dashboard_summary = {}
            if self.visualizer:
                dashboard_summary = await self.visualizer.create_dashboard_summary(
                    engagement_data, growth_data, behavior_data
                )
            
            # 인사이트 생성
            insights = await self.processor.generate_insights(recent_events)
            
            dashboard = {
                "summary": dashboard_summary,
                "engagement": engagement_data,
                "growth": growth_data,
                "behavior": behavior_data,
                "insights": [
                    {
                        "type": insight.type,
                        "title": insight.title,
                        "description": insight.description,
                        "value": insight.value,
                        "trend": insight.trend,
                        "confidence": insight.confidence,
                        "timestamp": insight.timestamp.isoformat()
                    }
                    for insight in insights
                ],
                "charts": charts,
                "realtime_stats": self.collector.get_realtime_stats(),
                "last_updated": datetime.now().isoformat(),
                "data_points": len(recent_events)
            }
            
            # 캐시 업데이트
            self._cached_dashboard = dashboard
            self._cache_timestamp = datetime.now()
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"실시간 대시보드 생성 실패: {e}")
            return {"error": str(e)}
    
    async def get_session_analytics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """세션별 분석"""
        try:
            if not self.collector or not self.processor:
                return {"error": "분석 시스템이 초기화되지 않았습니다"}
            
            # 세션 이벤트 가져오기
            events = await self.collector.get_events(
                session_id=session_id,
                limit=10000
            )
            
            if not events:
                return {"error": "해당 세션에 대한 데이터가 없습니다"}
            
            # 세션 정보
            sessions = await self.collector.get_sessions(limit=1 if session_id else 10)
            session_info = sessions[0] if sessions else None
            
            # 분석 수행
            engagement_data = await self.processor.analyze_engagement(events, time_window=86400)  # 24시간
            behavior_data = await self.processor.analyze_user_behavior(events)
            insights = await self.processor.generate_insights(events)
            
            # 세션 통계
            session_stats = await self.collector.get_statistics(session_id)
            
            return {
                "session_info": session_info.to_dict() if session_info else None,
                "engagement": engagement_data,
                "behavior": behavior_data,
                "statistics": session_stats,
                "insights": [
                    {
                        "type": insight.type,
                        "title": insight.title,
                        "description": insight.description,
                        "value": insight.value,
                        "trend": insight.trend,
                        "confidence": insight.confidence
                    }
                    for insight in insights
                ],
                "total_events": len(events),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"세션 분석 실패: {e}")
            return {"error": str(e)}
    
    async def get_historical_trends(self, days: int = 30) -> Dict[str, Any]:
        """과거 트렌드 분석"""
        try:
            if not self.collector or not self.processor:
                return {"error": "분석 시스템이 초기화되지 않았습니다"}
            
            # 과거 데이터 가져오기
            start_date = datetime.now() - timedelta(days=days)
            events = await self.collector.get_events(
                start_time=start_date,
                limit=50000
            )
            
            if not events:
                return {"error": "과거 데이터가 없습니다"}
            
            # 트렌드 분석
            growth_data = await self.processor.analyze_growth_trends(events, days=days)
            behavior_data = await self.processor.analyze_user_behavior(events)
            
            # 세션별 요약
            sessions = await self.collector.get_sessions(limit=days)
            session_summary = []
            
            for session in sessions:
                session_events = await self.collector.get_events(
                    session_id=session.session_id,
                    limit=10000
                )
                
                if session_events:
                    session_engagement = await self.processor.analyze_engagement(
                        session_events, time_window=86400
                    )
                    
                    session_summary.append({
                        "session_id": session.session_id,
                        "start_time": session.start_time.isoformat(),
                        "end_time": session.end_time.isoformat() if session.end_time else None,
                        "duration_hours": (
                            (session.end_time - session.start_time).total_seconds() / 3600
                            if session.end_time else 0
                        ),
                        "total_events": len(session_events),
                        "unique_users": session_engagement.get("unique_users", 0),
                        "engagement_score": session_engagement.get("engagement_score", 0)
                    })
            
            return {
                "period_days": days,
                "growth_trends": growth_data,
                "user_behavior": behavior_data,
                "session_summary": session_summary,
                "total_events": len(events),
                "total_sessions": len(sessions),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"과거 트렌드 분석 실패: {e}")
            return {"error": str(e)}
    
    async def export_analytics_data(self, 
                                   session_id: Optional[str] = None,
                                   format: str = "json") -> str:
        """분석 데이터 내보내기"""
        try:
            if not self.collector:
                raise Exception("데이터 수집기가 초기화되지 않았습니다")
            
            return await self.collector.export_data(session_id, format)
            
        except Exception as e:
            self.logger.error(f"데이터 내보내기 실패: {e}")
            raise
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭"""
        metrics = {
            "system_stats": self.stats,
            "available_chart_formats": self.visualizer.get_available_formats() if self.visualizer else []
        }
        
        if self.collector:
            metrics["collector_stats"] = self.collector.get_realtime_stats()
        
        return metrics
    
    def _is_cache_valid(self) -> bool:
        """캐시 유효성 확인"""
        if not self._cached_dashboard or not self._cache_timestamp:
            return False
        
        return (datetime.now() - self._cache_timestamp).total_seconds() < self.cache_duration
    
    async def _invalidate_cache(self):
        """캐시 무효화 (실시간 업데이트용)"""
        if self.real_time_analysis:
            self._cached_dashboard = None
            self._cache_timestamp = None
    
    def update_settings(self, settings: Dict[str, Any]):
        """설정 업데이트"""
        if "chart_format" in settings:
            self.chart_format = settings["chart_format"]
        
        if "theme" in settings:
            self.theme = settings["theme"]
            if self.visualizer:
                self.visualizer.set_theme(self.theme)
        
        if "real_time_analysis" in settings:
            self.real_time_analysis = settings["real_time_analysis"]
        
        if "cache_duration" in settings:
            self.cache_duration = max(10, settings["cache_duration"])  # 최소 10초
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        stats = self.stats.copy()
        
        stats.update({
            "enabled": self.enabled,
            "chart_format": self.chart_format,
            "theme": self.theme,
            "real_time_analysis": self.real_time_analysis,
            "cache_valid": self._is_cache_valid()
        })
        
        if self.collector:
            stats["collector"] = self.collector.get_realtime_stats()
        
        return stats
    
    async def cleanup(self):
        """리소스 정리"""
        if self.collector:
            await self.collector.cleanup()
        
        if self.processor:
            self.processor.clear_cache()
        
        self._cached_dashboard = None
        self._cache_timestamp = None
        
        self.logger.info("📊 분석 매니저 정리 완료")
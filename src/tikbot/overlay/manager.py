"""
오버레이 매니저 - Interactive Overlays 통합 관리
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

from .websocket import OverlayWebSocket
from .renderer import OverlayRenderer
from ..core.events import EventHandler, EventType


class OverlayManager:
    """Interactive Overlays 통합 매니저"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.enabled = config.get('enabled', True)
        
        # 컴포넌트들
        self.websocket_server: Optional[OverlayWebSocket] = None
        self.renderer: Optional[OverlayRenderer] = None
        
        # 설정
        self.websocket_host = config.get('websocket_host', 'localhost')
        self.websocket_port = config.get('websocket_port', 8080)
        self.templates_dir = config.get('templates_dir', 'templates')
        self.static_dir = config.get('static_dir', 'static')
        
        # 현재 목표 추적
        self.current_goals = {}
        
        # 통계
        self.stats = {
            "initialization_time": None,
            "websocket_connections": 0,
            "messages_sent": 0,
            "goals_created": 0,
            "templates_rendered": 0
        }
    
    async def initialize(self) -> bool:
        """오버레이 시스템 초기화"""
        if not self.enabled:
            self.logger.info("오버레이 시스템이 비활성화되어 있습니다.")
            return True
        
        try:
            import time
            start_time = time.time()
            
            # 렌더러 초기화
            self.renderer = OverlayRenderer(
                templates_dir=self.templates_dir,
                static_dir=self.static_dir,
                logger=self.logger
            )
            
            # WebSocket 서버 초기화
            self.websocket_server = OverlayWebSocket(
                host=self.websocket_host,
                port=self.websocket_port,
                logger=self.logger
            )
            
            # WebSocket 서버 시작
            success = await self.websocket_server.start()
            if not success:
                self.logger.error("WebSocket 서버 시작 실패")
                return False
            
            # 초기화 시간 기록
            self.stats["initialization_time"] = time.time() - start_time
            
            self.logger.info(f"🎨 오버레이 시스템 초기화 완료 ({self.stats['initialization_time']:.2f}초)")
            
            # 기본 목표 설정
            await self.create_default_goals()
            
            return True
            
        except Exception as e:
            self.logger.error(f"오버레이 시스템 초기화 실패: {e}")
            return False
    
    async def create_default_goals(self):
        """기본 목표들 생성"""
        default_goals = [
            {
                "id": "followers_100",
                "title": "팔로워 100명 달성",
                "description": "더 많은 팔로워를 얻어보세요!",
                "type": "followers",
                "target": 100,
                "active": True
            },
            {
                "id": "messages_500", 
                "title": "채팅 500개 달성",
                "description": "활발한 채팅으로 방송을 뜨겁게!",
                "type": "messages",
                "target": 500,
                "active": False
            },
            {
                "id": "gifts_50",
                "title": "선물 50개 받기",
                "description": "시청자들의 사랑을 받아보세요!",
                "type": "gifts",
                "target": 50,
                "active": False
            }
        ]
        
        for goal in default_goals:
            self.current_goals[goal["id"]] = goal
            self.stats["goals_created"] += 1
        
        self.logger.debug(f"기본 목표 {len(default_goals)}개 생성")
    
    def register_event_handlers(self, event_handler: EventHandler):
        """이벤트 핸들러에 오버레이 이벤트 등록"""
        if not self.enabled or not self.websocket_server:
            return
        
        # WebSocket 서버에 이벤트 등록
        self.websocket_server.register_event_handlers(event_handler)
        
        # 추가 목표 추적 핸들러들
        @event_handler.on(EventType.FOLLOW)
        async def on_follow_goal_update(event_data):
            await self.update_goal_progress("followers", 1)
        
        @event_handler.on(EventType.COMMENT)
        async def on_comment_goal_update(event_data):
            await self.update_goal_progress("messages", 1)
        
        @event_handler.on(EventType.GIFT) 
        async def on_gift_goal_update(event_data):
            gift_count = event_data.get("gift_count", 1)
            await self.update_goal_progress("gifts", gift_count)
        
        self.logger.info("오버레이 이벤트 핸들러 등록 완료")
    
    async def update_stats(self, stats: Dict[str, Any]):
        """통계 업데이트 및 오버레이 전송"""
        if not self.websocket_server:
            return
        
        # 업타임 포맷팅
        if "uptime_seconds" in stats:
            uptime_seconds = stats["uptime_seconds"]
            hours = uptime_seconds // 3600
            minutes = (uptime_seconds % 3600) // 60
            seconds = uptime_seconds % 60
            stats["uptime"] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        await self.websocket_server.update_stats(stats)
    
    async def update_goal_progress(self, goal_type: str, increment: int = 1):
        """목표 진행도 업데이트"""
        updated_goals = []
        
        for goal_id, goal in self.current_goals.items():
            if goal.get("type") == goal_type and goal.get("active", False):
                # 현재 값 증가
                current = goal.get("current", 0)
                goal["current"] = current + increment
                
                # 목표 달성 확인
                if goal["current"] >= goal["target"]:
                    goal["completed"] = True
                    goal["active"] = False  # 달성된 목표는 비활성화
                    self.logger.info(f"🎯 목표 달성: {goal['title']}")
                    
                    # 다음 목표 활성화
                    await self.activate_next_goal(goal_type)
                
                updated_goals.append(goal)
        
        # 업데이트된 목표들을 오버레이로 전송
        for goal in updated_goals:
            if self.websocket_server:
                await self.websocket_server.update_goal(goal)
    
    async def activate_next_goal(self, goal_type: str):
        """다음 목표 활성화"""
        # 같은 타입의 비활성 목표 찾기
        for goal_id, goal in self.current_goals.items():
            if (goal.get("type") == goal_type and 
                not goal.get("active", False) and 
                not goal.get("completed", False)):
                
                goal["active"] = True
                goal["current"] = 0
                
                self.logger.info(f"🎯 새 목표 활성화: {goal['title']}")
                
                if self.websocket_server:
                    await self.websocket_server.update_goal(goal)
                break
    
    def create_custom_goal(self, title: str, description: str, goal_type: str, 
                          target: int, goal_id: Optional[str] = None) -> str:
        """사용자 정의 목표 생성"""
        if goal_id is None:
            goal_id = f"custom_{goal_type}_{target}"
        
        goal = {
            "id": goal_id,
            "title": title,
            "description": description, 
            "type": goal_type,
            "target": target,
            "current": 0,
            "active": True,
            "custom": True
        }
        
        # 같은 타입의 기존 목표 비활성화
        for existing_goal in self.current_goals.values():
            if existing_goal.get("type") == goal_type:
                existing_goal["active"] = False
        
        self.current_goals[goal_id] = goal
        self.stats["goals_created"] += 1
        
        self.logger.info(f"사용자 정의 목표 생성: {title}")
        return goal_id
    
    def get_overlay_urls(self, base_url: str = None) -> Dict[str, str]:
        """오버레이 URL 목록 반환"""
        if base_url is None:
            # API 서버 URL 사용
            api_config = self.config.get('api', {})
            host = api_config.get('host', 'localhost')
            port = api_config.get('port', 8000)
            base_url = f"http://{host}:{port}"
        
        if self.renderer:
            return self.renderer.get_overlay_urls(base_url)
        else:
            return {}
    
    def render_overlay_template(self, template_name: str, **context) -> str:
        """오버레이 템플릿 렌더링"""
        if not self.renderer:
            return "<html><body><h1>렌더러가 초기화되지 않았습니다</h1></body></html>"
        
        # WebSocket URL 추가
        websocket_url = f"ws://{self.websocket_host}:{self.websocket_port}"
        context.setdefault('websocket_url', websocket_url)
        
        # 기본 설정들 추가
        context.setdefault('max_messages', self.config.get('max_messages', 20))
        
        result = self.renderer.render_template(template_name, **context)
        self.stats["templates_rendered"] += 1
        
        return result
    
    async def broadcast_custom_event(self, event_type: str, data: Dict[str, Any]):
        """사용자 정의 이벤트 브로드캐스트"""
        if self.websocket_server:
            from .websocket import OverlayEvent
            event = OverlayEvent(type=event_type, data=data)
            await self.websocket_server.broadcast(event)
    
    def get_active_goals(self) -> List[Dict[str, Any]]:
        """활성 목표 목록 반환"""
        return [goal for goal in self.current_goals.values() if goal.get("active", False)]
    
    def get_completed_goals(self) -> List[Dict[str, Any]]:
        """완료된 목표 목록 반환"""
        return [goal for goal in self.current_goals.values() if goal.get("completed", False)]
    
    def get_stats(self) -> Dict[str, Any]:
        """오버레이 매니저 통계 반환"""
        stats = self.stats.copy()
        
        if self.websocket_server:
            ws_stats = self.websocket_server.get_stats()
            stats.update({f"websocket_{k}": v for k, v in ws_stats.items()})
        
        stats.update({
            "enabled": self.enabled,
            "websocket_url": f"ws://{self.websocket_host}:{self.websocket_port}",
            "active_goals": len(self.get_active_goals()),
            "completed_goals": len(self.get_completed_goals()),
            "total_goals": len(self.current_goals)
        })
        
        return stats
    
    async def cleanup(self):
        """리소스 정리"""
        if self.websocket_server:
            await self.websocket_server.stop()
        
        self.logger.info("오버레이 매니저 정리 완료")
"""
오버레이 WebSocket 서버 - 실시간 데이터 전송
"""

import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any, Set, List
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

from ..core.events import EventHandler, EventType


@dataclass
class OverlayEvent:
    """오버레이 이벤트 데이터"""
    type: str
    data: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(asdict(self), ensure_ascii=False)


class OverlayWebSocket:
    """오버레이 WebSocket 서버"""
    
    def __init__(self, host: str = "localhost", port: int = 8080, 
                 logger: Optional[logging.Logger] = None):
        self.host = host
        self.port = port
        self.logger = logger or logging.getLogger(__name__)
        
        # WebSocket 연결 관리
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server = None
        self.is_running = False
        
        # 데이터 캐시 (새 클라이언트 연결시 전송)
        self.cached_data = {
            "stats": {},
            "recent_events": [],
            "current_goal": None,
            "leaderboard": []
        }
        
        # 통계
        self.stats = {
            "clients_connected": 0,
            "total_connections": 0,
            "messages_sent": 0,
            "errors": 0
        }
        
        if not WEBSOCKETS_AVAILABLE:
            self.logger.warning("websockets 라이브러리가 설치되지 않았습니다.")
    
    async def start(self) -> bool:
        """WebSocket 서버 시작"""
        if not WEBSOCKETS_AVAILABLE:
            self.logger.error("websockets를 사용할 수 없습니다.")
            return False
        
        if self.is_running:
            return True
        
        try:
            self.server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10
            )
            
            self.is_running = True
            self.logger.info(f"🌐 오버레이 WebSocket 서버 시작: ws://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"WebSocket 서버 시작 실패: {e}")
            return False
    
    async def stop(self):
        """WebSocket 서버 중지"""
        if not self.is_running:
            return
        
        # 모든 클라이언트 연결 종료
        if self.clients:
            await asyncio.gather(
                *[client.close() for client in self.clients.copy()],
                return_exceptions=True
            )
        
        # 서버 종료
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        self.is_running = False
        self.clients.clear()
        self.logger.info("오버레이 WebSocket 서버 종료")
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """클라이언트 연결 처리"""
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        self.logger.info(f"새 오버레이 클라이언트 연결: {client_ip}")
        
        # 클라이언트 등록
        self.clients.add(websocket)
        self.stats["clients_connected"] += 1
        self.stats["total_connections"] += 1
        
        try:
            # 초기 데이터 전송
            await self.send_initial_data(websocket)
            
            # 클라이언트 메시지 처리 루프
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_client_message(websocket, data)
                except json.JSONDecodeError:
                    self.logger.warning(f"잘못된 JSON 메시지: {message}")
                except Exception as e:
                    self.logger.error(f"클라이언트 메시지 처리 오류: {e}")
        
        except websockets.exceptions.ConnectionClosedError:
            pass
        except Exception as e:
            self.logger.error(f"클라이언트 처리 오류: {e}")
            self.stats["errors"] += 1
        
        finally:
            # 클라이언트 연결 해제
            self.clients.discard(websocket)
            self.stats["clients_connected"] -= 1
            self.logger.info(f"오버레이 클라이언트 연결 해제: {client_ip}")
    
    async def send_initial_data(self, websocket: WebSocketServerProtocol):
        """새 클라이언트에게 초기 데이터 전송"""
        try:
            # 현재 통계 전송
            if self.cached_data["stats"]:
                await self.send_to_client(websocket, OverlayEvent(
                    type="stats_update",
                    data=self.cached_data["stats"]
                ))
            
            # 최근 이벤트 전송
            for event_data in self.cached_data["recent_events"][-20:]:  # 최근 20개
                await self.send_to_client(websocket, OverlayEvent(
                    type="recent_event",
                    data=event_data
                ))
            
            # 현재 목표 전송
            if self.cached_data["current_goal"]:
                await self.send_to_client(websocket, OverlayEvent(
                    type="goal_update",
                    data=self.cached_data["current_goal"]
                ))
            
            self.logger.debug("초기 데이터 전송 완료")
            
        except Exception as e:
            self.logger.error(f"초기 데이터 전송 실패: {e}")
    
    async def handle_client_message(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """클라이언트로부터 받은 메시지 처리"""
        message_type = data.get("type")
        
        if message_type == "ping":
            # 핑 응답
            await self.send_to_client(websocket, OverlayEvent(
                type="pong",
                data={"timestamp": time.time()}
            ))
        
        elif message_type == "request_data":
            # 데이터 요청
            data_type = data.get("data_type")
            if data_type == "stats":
                await self.send_to_client(websocket, OverlayEvent(
                    type="stats_update",
                    data=self.cached_data["stats"]
                ))
            elif data_type == "recent_events":
                await self.send_to_client(websocket, OverlayEvent(
                    type="recent_events",
                    data=self.cached_data["recent_events"][-50:]
                ))
        
        else:
            self.logger.warning(f"알 수 없는 메시지 타입: {message_type}")
    
    async def send_to_client(self, websocket: WebSocketServerProtocol, event: OverlayEvent):
        """특정 클라이언트에게 메시지 전송"""
        try:
            await websocket.send(event.to_json())
            self.stats["messages_sent"] += 1
        except websockets.exceptions.ConnectionClosedError:
            pass
        except Exception as e:
            self.logger.error(f"클라이언트 전송 오류: {e}")
    
    async def broadcast(self, event: OverlayEvent):
        """모든 클라이언트에게 메시지 브로드캐스트"""
        if not self.clients:
            return
        
        # 끊어진 연결 제거
        disconnected = set()
        
        for client in self.clients.copy():
            try:
                await client.send(event.to_json())
                self.stats["messages_sent"] += 1
            except websockets.exceptions.ConnectionClosedError:
                disconnected.add(client)
            except Exception as e:
                self.logger.error(f"브로드캐스트 오류: {e}")
                disconnected.add(client)
        
        # 끊어진 연결 정리
        for client in disconnected:
            self.clients.discard(client)
            self.stats["clients_connected"] -= 1
    
    def register_event_handlers(self, event_handler: EventHandler):
        """이벤트 핸들러에 오버레이 이벤트 등록"""
        
        @event_handler.on(EventType.COMMENT)
        async def on_comment_overlay(event_data):
            # 채팅 메시지를 오버레이로 전송
            overlay_event = OverlayEvent(
                type="new_comment",
                data={
                    "username": event_data.get("username", ""),
                    "nickname": event_data.get("nickname", ""),
                    "comment": event_data.get("comment", ""),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # 최근 이벤트에 추가
            self.cached_data["recent_events"].append(overlay_event.data)
            if len(self.cached_data["recent_events"]) > 100:
                self.cached_data["recent_events"] = self.cached_data["recent_events"][-100:]
            
            await self.broadcast(overlay_event)
        
        @event_handler.on(EventType.GIFT)
        async def on_gift_overlay(event_data):
            # 선물 이벤트를 오버레이로 전송
            overlay_event = OverlayEvent(
                type="new_gift",
                data={
                    "username": event_data.get("username", ""),
                    "nickname": event_data.get("nickname", ""),
                    "gift_name": event_data.get("gift_name", ""),
                    "gift_count": event_data.get("gift_count", 1),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            self.cached_data["recent_events"].append(overlay_event.data)
            if len(self.cached_data["recent_events"]) > 100:
                self.cached_data["recent_events"] = self.cached_data["recent_events"][-100:]
            
            await self.broadcast(overlay_event)
        
        @event_handler.on(EventType.FOLLOW)
        async def on_follow_overlay(event_data):
            # 팔로우 이벤트를 오버레이로 전송
            overlay_event = OverlayEvent(
                type="new_follow",
                data={
                    "username": event_data.get("username", ""),
                    "nickname": event_data.get("nickname", ""),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            self.cached_data["recent_events"].append(overlay_event.data)
            if len(self.cached_data["recent_events"]) > 100:
                self.cached_data["recent_events"] = self.cached_data["recent_events"][-100:]
            
            await self.broadcast(overlay_event)
        
        self.logger.info("오버레이 이벤트 핸들러 등록 완료")
    
    async def update_stats(self, stats: Dict[str, Any]):
        """통계 업데이트 및 브로드캐스트"""
        self.cached_data["stats"] = stats
        
        overlay_event = OverlayEvent(
            type="stats_update",
            data=stats
        )
        
        await self.broadcast(overlay_event)
    
    async def update_goal(self, goal_data: Dict[str, Any]):
        """목표 업데이트 및 브로드캐스트"""
        self.cached_data["current_goal"] = goal_data
        
        overlay_event = OverlayEvent(
            type="goal_update",
            data=goal_data
        )
        
        await self.broadcast(overlay_event)
    
    def get_stats(self) -> Dict[str, Any]:
        """WebSocket 서버 통계 반환"""
        return {
            **self.stats,
            "is_running": self.is_running,
            "server_url": f"ws://{self.host}:{self.port}",
            "websockets_available": WEBSOCKETS_AVAILABLE
        }
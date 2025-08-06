"""
TikBot FastAPI 서버
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..core.config import BotConfig
from ..core.events import EventType


class CommandRequest(BaseModel):
    """명령어 추가/수정 요청"""
    command: str
    response: str


class AutoResponseRequest(BaseModel):
    """자동 응답 추가/수정 요청"""
    keyword: str
    responses: List[str]


class StatsResponse(BaseModel):
    """통계 응답"""
    messages_received: int
    commands_processed: int
    auto_responses_sent: int
    gifts_received: int
    followers_gained: int
    spam_filtered: int
    uptime: Optional[str]
    start_time: Optional[str]
    is_running: bool


class EventResponse(BaseModel):
    """이벤트 응답"""
    type: str
    data: Dict[str, Any]
    timestamp: str


def create_app(config: BotConfig, logger: logging.Logger) -> FastAPI:
    """FastAPI 앱 생성"""
    
    app = FastAPI(
        title="TikBot API",
        description="TikTok Live Bot REST API",
        version="0.1.0"
    )
    
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 정적 파일 서빙
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except RuntimeError:
        # static 디렉토리가 없을 경우 무시
        pass
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """대시보드 홈페이지"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>TikBot Dashboard</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
                .container { max-width: 1200px; margin: 0 auto; }
                .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
                .stat { text-align: center; padding: 15px; background: #f8f9fa; border-radius: 6px; }
                .stat-value { font-size: 2em; font-weight: bold; color: #007bff; }
                .stat-label { color: #666; margin-top: 5px; }
                h1 { color: #333; text-align: center; }
                .status { padding: 10px; border-radius: 6px; text-align: center; font-weight: bold; }
                .status.running { background: #d4edda; color: #155724; }
                .status.stopped { background: #f8d7da; color: #721c24; }
                .btn { padding: 8px 16px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
                .btn-primary { background: #007bff; color: white; }
                .btn-success { background: #28a745; color: white; }
                .btn-danger { background: #dc3545; color: white; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 TikBot Dashboard</h1>
                
                <div class="card">
                    <h2>봇 상태</h2>
                    <div id="status" class="status">로딩 중...</div>
                </div>
                
                <div class="card">
                    <h2>📊 실시간 통계</h2>
                    <div class="stats" id="stats">
                        <div class="stat">
                            <div class="stat-value" id="messages">0</div>
                            <div class="stat-label">받은 메시지</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="commands">0</div>
                            <div class="stat-label">처리한 명령어</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="gifts">0</div>
                            <div class="stat-label">받은 선물</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="followers">0</div>
                            <div class="stat-label">새 팔로워</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🔧 관리</h2>
                    <button class="btn btn-primary" onclick="refreshStats()">통계 새로고침</button>
                    <button class="btn btn-success" onclick="window.open('/api/events', '_blank')">이벤트 로그</button>
                    <button class="btn btn-primary" onclick="window.open('/docs', '_blank')">API 문서</button>
                </div>
            </div>
            
            <script>
                async function refreshStats() {
                    try {
                        const response = await fetch('/api/stats');
                        const data = await response.json();
                        
                        document.getElementById('messages').textContent = data.messages_received;
                        document.getElementById('commands').textContent = data.commands_processed;
                        document.getElementById('gifts').textContent = data.gifts_received;
                        document.getElementById('followers').textContent = data.followers_gained;
                        
                        const statusEl = document.getElementById('status');
                        if (data.is_running) {
                            statusEl.textContent = `✅ 실행 중 (${data.uptime || '0:00:00'})`;
                            statusEl.className = 'status running';
                        } else {
                            statusEl.textContent = '🔴 중지됨';
                            statusEl.className = 'status stopped';
                        }
                    } catch (error) {
                        console.error('통계 로드 실패:', error);
                    }
                }
                
                // 페이지 로드시 통계 로드
                refreshStats();
                
                // 5초마다 자동 새로고침
                setInterval(refreshStats, 5000);
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    @app.get("/health")
    async def health_check():
        """헬스 체크"""
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    @app.get("/api/stats", response_model=StatsResponse)
    async def get_stats():
        """봇 통계 조회"""
        if not hasattr(app.state, 'bot'):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bot not initialized"
            )
        
        stats = app.state.bot.get_stats()
        return StatsResponse(**stats)
    
    @app.get("/api/events", response_model=List[EventResponse])
    async def get_events(
        event_type: Optional[str] = None,
        limit: int = 100
    ):
        """이벤트 히스토리 조회"""
        if not hasattr(app.state, 'bot'):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bot not initialized"
            )
        
        filter_type = None
        if event_type:
            try:
                filter_type = EventType(event_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid event type: {event_type}"
                )
        
        events = app.state.bot.event_handler.get_event_history(filter_type, limit)
        
        return [
            EventResponse(
                type=event.type.value,
                data=event.data,
                timestamp=event.timestamp.isoformat()
            )
            for event in events
        ]
    
    @app.get("/api/config")
    async def get_config():
        """현재 설정 조회"""
        return config.model_dump()
    
    @app.post("/api/commands")
    async def add_command(request: CommandRequest):
        """명령어 추가/수정"""
        if not hasattr(app.state, 'bot'):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bot not initialized"
            )
        
        app.state.bot.add_command(request.command, request.response)
        logger.info(f"명령어 추가: {request.command} -> {request.response}")
        
        return {"message": "명령어가 추가되었습니다", "command": request.command}
    
    @app.delete("/api/commands/{command}")
    async def remove_command(command: str):
        """명령어 제거"""
        if not hasattr(app.state, 'bot'):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bot not initialized"
            )
        
        if command not in app.state.bot.config.commands:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="명령어를 찾을 수 없습니다"
            )
        
        app.state.bot.remove_command(command)
        logger.info(f"명령어 제거: {command}")
        
        return {"message": "명령어가 제거되었습니다", "command": command}
    
    @app.post("/api/auto-responses")
    async def add_auto_response(request: AutoResponseRequest):
        """자동 응답 추가/수정"""
        if not hasattr(app.state, 'bot'):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bot not initialized"
            )
        
        app.state.bot.add_auto_response(request.keyword, request.responses)
        logger.info(f"자동 응답 추가: {request.keyword} -> {request.responses}")
        
        return {"message": "자동 응답이 추가되었습니다", "keyword": request.keyword}
    
    @app.delete("/api/auto-responses/{keyword}")
    async def remove_auto_response(keyword: str):
        """자동 응답 제거"""
        if not hasattr(app.state, 'bot'):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bot not initialized"
            )
        
        if keyword not in app.state.bot.config.auto_responses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="자동 응답을 찾을 수 없습니다"
            )
        
        app.state.bot.remove_auto_response(keyword)
        logger.info(f"자동 응답 제거: {keyword}")
        
        return {"message": "자동 응답이 제거되었습니다", "keyword": keyword}
    
    # 오버레이 라우트들
    @app.get("/overlay/chat", response_class=HTMLResponse)
    async def overlay_chat():
        """채팅 오버레이"""
        if hasattr(app.state, 'bot') and app.state.bot._overlay_manager:
            return app.state.bot._overlay_manager.render_overlay_template("chat_overlay.html")
        return "<html><body><h1>오버레이 시스템이 비활성화되어 있습니다</h1></body></html>"
    
    @app.get("/overlay/stats", response_class=HTMLResponse)
    async def overlay_stats():
        """통계 오버레이"""
        if hasattr(app.state, 'bot') and app.state.bot._overlay_manager:
            return app.state.bot._overlay_manager.render_overlay_template("stats_overlay.html")
        return "<html><body><h1>오버레이 시스템이 비활성화되어 있습니다</h1></body></html>"
    
    @app.get("/overlay/goal", response_class=HTMLResponse)
    async def overlay_goal():
        """목표 오버레이"""
        if hasattr(app.state, 'bot') and app.state.bot._overlay_manager:
            return app.state.bot._overlay_manager.render_overlay_template("goal_overlay.html")
        return "<html><body><h1>오버레이 시스템이 비활성화되어 있습니다</h1></body></html>"
    
    @app.get("/overlay/alerts", response_class=HTMLResponse)
    async def overlay_alerts():
        """알림 오버레이"""
        if hasattr(app.state, 'bot') and app.state.bot._overlay_manager:
            return app.state.bot._overlay_manager.render_overlay_template("alerts_overlay.html")
        return "<html><body><h1>오버레이 시스템이 비활성화되어 있습니다</h1></body></html>"
    
    @app.get("/overlay/dashboard", response_class=HTMLResponse)
    async def overlay_dashboard():
        """통합 대시보드"""
        if hasattr(app.state, 'bot') and app.state.bot._overlay_manager:
            return app.state.bot._overlay_manager.render_overlay_template("dashboard.html")
        return "<html><body><h1>오버레이 시스템이 비활성화되어 있습니다</h1></body></html>"
    
    @app.get("/overlay/urls")
    async def get_overlay_urls():
        """오버레이 URL 목록"""
        if hasattr(app.state, 'bot') and app.state.bot._overlay_manager:
            base_url = f"http://{config.api.host}:{config.api.port}"
            return app.state.bot._overlay_manager.get_overlay_urls(base_url)
        return {"error": "오버레이 시스템이 비활성화되어 있습니다"}
    
    @app.post("/overlay/goal")
    async def create_custom_goal(
        title: str,
        description: str = "",
        goal_type: str = "custom",
        target: int = 100
    ):
        """사용자 정의 목표 생성"""
        if not hasattr(app.state, 'bot') or not app.state.bot._overlay_manager:
            raise HTTPException(status_code=503, detail="오버레이 시스템이 비활성화되어 있습니다")
        
        goal_id = app.state.bot._overlay_manager.create_custom_goal(
            title=title,
            description=description,
            goal_type=goal_type,
            target=target
        )
        
        return {"message": "목표가 생성되었습니다", "goal_id": goal_id}
    
    @app.get("/overlay/goals")
    async def get_goals():
        """목표 목록 조회"""
        if not hasattr(app.state, 'bot') or not app.state.bot._overlay_manager:
            raise HTTPException(status_code=503, detail="오버레이 시스템이 비활성화되어 있습니다")
        
        overlay_manager = app.state.bot._overlay_manager
        return {
            "active_goals": overlay_manager.get_active_goals(),
            "completed_goals": overlay_manager.get_completed_goals()
        }
    
    @app.get("/overlay/stats")
    async def get_overlay_stats():
        """오버레이 시스템 통계"""
        if not hasattr(app.state, 'bot') or not app.state.bot._overlay_manager:
            raise HTTPException(status_code=503, detail="오버레이 시스템이 비활성화되어 있습니다")
        
        return app.state.bot._overlay_manager.get_stats()
    
    # 정적 파일 서빙
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except RuntimeError:
        # static 디렉토리가 없는 경우 무시
        pass
    
    return app
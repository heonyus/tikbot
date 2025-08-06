"""
오버레이 렌더러 - HTML/CSS/JS 템플릿 생성
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


class OverlayRenderer:
    """오버레이 HTML 렌더러"""
    
    def __init__(self, templates_dir: str = "templates", 
                 static_dir: str = "static",
                 logger: Optional[logging.Logger] = None):
        self.templates_dir = Path(templates_dir)
        self.static_dir = Path(static_dir) 
        self.logger = logger or logging.getLogger(__name__)
        
        # Jinja2 환경 설정
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 디렉토리 생성
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        (self.templates_dir / "overlay").mkdir(exist_ok=True)
        self.static_dir.mkdir(parents=True, exist_ok=True)
        (self.static_dir / "css").mkdir(exist_ok=True)
        (self.static_dir / "js").mkdir(exist_ok=True)
        
        self._create_default_templates()
    
    def _create_default_templates(self):
        """기본 오버레이 템플릿들 생성"""
        templates = {
            "chat_overlay.html": self._get_chat_overlay_template(),
            "stats_overlay.html": self._get_stats_overlay_template(),
            "goal_overlay.html": self._get_goal_overlay_template(),
            "alerts_overlay.html": self._get_alerts_overlay_template(),
            "dashboard.html": self._get_dashboard_template()
        }
        
        for filename, content in templates.items():
            template_path = self.templates_dir / "overlay" / filename
            if not template_path.exists():
                template_path.write_text(content, encoding='utf-8')
                self.logger.debug(f"기본 템플릿 생성: {filename}")
        
        # CSS/JS 파일도 생성
        self._create_default_styles()
        self._create_default_scripts()
    
    def _get_chat_overlay_template(self) -> str:
        """채팅 오버레이 템플릿"""
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikBot - 채팅 오버레이</title>
    <link rel="stylesheet" href="/static/css/overlay.css">
</head>
<body class="overlay-body">
    <div id="chat-container" class="chat-container">
        <h3 class="overlay-title">💬 실시간 채팅</h3>
        <div id="chat-messages" class="chat-messages">
            <!-- 채팅 메시지들이 여기에 표시됩니다 -->
        </div>
    </div>
    
    <script src="/static/js/overlay-websocket.js"></script>
    <script>
        const chatOverlay = new OverlayWebSocket('{{ websocket_url }}');
        
        chatOverlay.on('new_comment', function(data) {
            addChatMessage(data);
        });
        
        function addChatMessage(data) {
            const messagesContainer = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'chat-message';
            
            const timestamp = new Date(data.timestamp).toLocaleTimeString();
            
            messageDiv.innerHTML = `
                <div class="message-header">
                    <span class="username">${escapeHtml(data.nickname || data.username)}</span>
                    <span class="timestamp">${timestamp}</span>
                </div>
                <div class="message-content">${escapeHtml(data.comment)}</div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            
            // 최대 메시지 수 제한
            const messages = messagesContainer.querySelectorAll('.chat-message');
            if (messages.length > {{ max_messages | default(20) }}) {
                messages[0].remove();
            }
            
            // 스크롤을 맨 아래로
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            // 애니메이션 효과
            messageDiv.style.opacity = '0';
            messageDiv.style.transform = 'translateX(20px)';
            setTimeout(() => {
                messageDiv.style.transition = 'all 0.3s ease';
                messageDiv.style.opacity = '1';
                messageDiv.style.transform = 'translateX(0)';
            }, 10);
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>'''
    
    def _get_stats_overlay_template(self) -> str:
        """통계 오버레이 템플릿"""
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikBot - 통계 오버레이</title>
    <link rel="stylesheet" href="/static/css/overlay.css">
</head>
<body class="overlay-body">
    <div id="stats-container" class="stats-container">
        <h3 class="overlay-title">📊 실시간 통계</h3>
        
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-icon">💬</div>
                <div class="stat-value" id="messages-count">0</div>
                <div class="stat-label">메시지</div>
            </div>
            
            <div class="stat-item">
                <div class="stat-icon">👥</div>
                <div class="stat-value" id="followers-count">0</div>
                <div class="stat-label">팔로워</div>
            </div>
            
            <div class="stat-item">
                <div class="stat-icon">🎁</div>
                <div class="stat-value" id="gifts-count">0</div>
                <div class="stat-label">선물</div>
            </div>
            
            <div class="stat-item">
                <div class="stat-icon">⏱️</div>
                <div class="stat-value" id="uptime">00:00:00</div>
                <div class="stat-label">방송시간</div>
            </div>
        </div>
    </div>
    
    <script src="/static/js/overlay-websocket.js"></script>
    <script>
        const statsOverlay = new OverlayWebSocket('{{ websocket_url }}');
        
        statsOverlay.on('stats_update', function(data) {
            updateStats(data);
        });
        
        function updateStats(stats) {
            document.getElementById('messages-count').textContent = 
                stats.messages_received || 0;
            document.getElementById('followers-count').textContent = 
                stats.followers_gained || 0;
            document.getElementById('gifts-count').textContent = 
                stats.gifts_received || 0;
            
            if (stats.uptime) {
                document.getElementById('uptime').textContent = stats.uptime;
            }
        }
        
        // 업타임 카운터 (서버에서 받지 않는 경우)
        let startTime = Date.now();
        setInterval(() => {
            const elapsed = Date.now() - startTime;
            const hours = Math.floor(elapsed / 3600000);
            const minutes = Math.floor((elapsed % 3600000) / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            
            const uptime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            if (!document.getElementById('uptime').textContent.includes(':')) {
                document.getElementById('uptime').textContent = uptime;
            }
        }, 1000);
    </script>
</body>
</html>'''
    
    def _get_goal_overlay_template(self) -> str:
        """목표 달성 오버레이 템플릿"""
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikBot - 목표 오버레이</title>
    <link rel="stylesheet" href="/static/css/overlay.css">
</head>
<body class="overlay-body">
    <div id="goal-container" class="goal-container" style="display: none;">
        <h3 class="overlay-title">🎯 목표 달성</h3>
        
        <div class="goal-info">
            <div class="goal-title" id="goal-title">팔로워 100명 달성!</div>
            <div class="goal-description" id="goal-description">현재 목표를 향해 달려갑니다!</div>
        </div>
        
        <div class="progress-container">
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
            </div>
            <div class="progress-text">
                <span id="current-value">0</span> / <span id="target-value">100</span>
                (<span id="progress-percent">0</span>%)
            </div>
        </div>
    </div>
    
    <script src="/static/js/overlay-websocket.js"></script>
    <script>
        const goalOverlay = new OverlayWebSocket('{{ websocket_url }}');
        
        goalOverlay.on('goal_update', function(data) {
            updateGoal(data);
        });
        
        function updateGoal(goal) {
            const container = document.getElementById('goal-container');
            
            if (!goal || !goal.active) {
                container.style.display = 'none';
                return;
            }
            
            container.style.display = 'block';
            
            document.getElementById('goal-title').textContent = goal.title || '목표';
            document.getElementById('goal-description').textContent = goal.description || '';
            
            const current = goal.current || 0;
            const target = goal.target || 100;
            const percent = Math.min(100, Math.round((current / target) * 100));
            
            document.getElementById('current-value').textContent = current;
            document.getElementById('target-value').textContent = target;
            document.getElementById('progress-percent').textContent = percent;
            
            const progressFill = document.getElementById('progress-fill');
            progressFill.style.width = percent + '%';
            
            // 목표 달성 애니메이션
            if (percent >= 100) {
                progressFill.classList.add('goal-completed');
                setTimeout(() => {
                    container.classList.add('goal-achieved');
                }, 500);
            }
        }
    </script>
</body>
</html>'''
    
    def _get_alerts_overlay_template(self) -> str:
        """알림 오버레이 템플릿"""
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikBot - 알림 오버레이</title>
    <link rel="stylesheet" href="/static/css/overlay.css">
</head>
<body class="overlay-body">
    <div id="alerts-container" class="alerts-container">
        <!-- 알림들이 여기에 표시됩니다 -->
    </div>
    
    <script src="/static/js/overlay-websocket.js"></script>
    <script>
        const alertsOverlay = new OverlayWebSocket('{{ websocket_url }}');
        
        alertsOverlay.on('new_follow', function(data) {
            showAlert('follow', `🎉 ${data.nickname}님이 팔로우했습니다!`);
        });
        
        alertsOverlay.on('new_gift', function(data) {
            const message = `🎁 ${data.nickname}님이 ${data.gift_name} ${data.gift_count}개를 보냈습니다!`;
            showAlert('gift', message);
        });
        
        function showAlert(type, message) {
            const container = document.getElementById('alerts-container');
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type}`;
            alertDiv.textContent = message;
            
            container.appendChild(alertDiv);
            
            // 애니메이션
            setTimeout(() => {
                alertDiv.classList.add('alert-show');
            }, 10);
            
            // 5초 후 제거
            setTimeout(() => {
                alertDiv.classList.add('alert-hide');
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.parentNode.removeChild(alertDiv);
                    }
                }, 500);
            }, 5000);
        }
    </script>
</body>
</html>'''
    
    def _get_dashboard_template(self) -> str:
        """통합 대시보드 템플릿"""
        return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikBot - 방송 대시보드</title>
    <link rel="stylesheet" href="/static/css/overlay.css">
    <style>
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: auto auto;
            gap: 20px;
            padding: 20px;
            height: 100vh;
            box-sizing: border-box;
        }
        
        .dashboard-section {
            background: rgba(0, 0, 0, 0.8);
            border-radius: 10px;
            padding: 15px;
            border: 2px solid #00d4ff;
        }
        
        .section-title {
            color: #00d4ff;
            margin-bottom: 15px;
            font-size: 18px;
            font-weight: bold;
        }
    </style>
</head>
<body class="overlay-body">
    <div class="dashboard-grid">
        <!-- 실시간 채팅 -->
        <div class="dashboard-section">
            <div class="section-title">💬 실시간 채팅</div>
            <div id="chat-messages" class="chat-messages" style="height: 300px; overflow-y: auto;">
                <!-- 채팅 메시지들 -->
            </div>
        </div>
        
        <!-- 통계 -->
        <div class="dashboard-section">
            <div class="section-title">📊 방송 통계</div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-icon">💬</div>
                    <div class="stat-value" id="messages-count">0</div>
                    <div class="stat-label">메시지</div>
                </div>
                <div class="stat-item">
                    <div class="stat-icon">👥</div>
                    <div class="stat-value" id="followers-count">0</div>
                    <div class="stat-label">팔로워</div>
                </div>
                <div class="stat-item">
                    <div class="stat-icon">🎁</div>
                    <div class="stat-value" id="gifts-count">0</div>
                    <div class="stat-label">선물</div>
                </div>
                <div class="stat-item">
                    <div class="stat-icon">⏱️</div>
                    <div class="stat-value" id="uptime">00:00:00</div>
                    <div class="stat-label">방송시간</div>
                </div>
            </div>
        </div>
        
        <!-- 목표 추적 -->
        <div class="dashboard-section">
            <div class="section-title">🎯 목표 달성</div>
            <div id="goal-section">
                <div class="goal-info">
                    <div class="goal-title" id="goal-title">목표를 설정해보세요!</div>
                    <div class="goal-description" id="goal-description">방송 목표를 달성해 나가세요.</div>
                </div>
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
                    </div>
                    <div class="progress-text">
                        <span id="current-value">0</span> / <span id="target-value">100</span>
                        (<span id="progress-percent">0</span>%)
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 최근 알림 -->
        <div class="dashboard-section">
            <div class="section-title">🔔 최근 알림</div>
            <div id="recent-alerts" style="height: 300px; overflow-y: auto;">
                <!-- 최근 알림들 -->
            </div>
        </div>
    </div>
    
    <script src="/static/js/overlay-websocket.js"></script>
    <script>
        const dashboard = new OverlayWebSocket('{{ websocket_url }}');
        
        // 채팅 메시지 처리
        dashboard.on('new_comment', function(data) {
            addChatMessage(data);
        });
        
        // 통계 업데이트
        dashboard.on('stats_update', function(data) {
            updateStats(data);
        });
        
        // 목표 업데이트
        dashboard.on('goal_update', function(data) {
            updateGoal(data);
        });
        
        // 새 팔로우 알림
        dashboard.on('new_follow', function(data) {
            addAlert('follow', `🎉 ${data.nickname}님이 팔로우했습니다!`);
        });
        
        // 선물 알림
        dashboard.on('new_gift', function(data) {
            const message = `🎁 ${data.nickname}님이 ${data.gift_name} ${data.gift_count}개를 보냈습니다!`;
            addAlert('gift', message);
        });
        
        function addChatMessage(data) {
            const container = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'chat-message';
            
            const timestamp = new Date(data.timestamp).toLocaleTimeString();
            messageDiv.innerHTML = `
                <div class="message-header">
                    <span class="username">${escapeHtml(data.nickname || data.username)}</span>
                    <span class="timestamp">${timestamp}</span>
                </div>
                <div class="message-content">${escapeHtml(data.comment)}</div>
            `;
            
            container.appendChild(messageDiv);
            
            // 메시지 수 제한
            const messages = container.querySelectorAll('.chat-message');
            if (messages.length > 20) {
                messages[0].remove();
            }
            
            container.scrollTop = container.scrollHeight;
        }
        
        function updateStats(stats) {
            document.getElementById('messages-count').textContent = stats.messages_received || 0;
            document.getElementById('followers-count').textContent = stats.followers_gained || 0;
            document.getElementById('gifts-count').textContent = stats.gifts_received || 0;
            
            if (stats.uptime) {
                document.getElementById('uptime').textContent = stats.uptime;
            }
        }
        
        function updateGoal(goal) {
            if (!goal || !goal.active) return;
            
            document.getElementById('goal-title').textContent = goal.title || '목표';
            document.getElementById('goal-description').textContent = goal.description || '';
            
            const current = goal.current || 0;
            const target = goal.target || 100;
            const percent = Math.min(100, Math.round((current / target) * 100));
            
            document.getElementById('current-value').textContent = current;
            document.getElementById('target-value').textContent = target;
            document.getElementById('progress-percent').textContent = percent;
            document.getElementById('progress-fill').style.width = percent + '%';
        }
        
        function addAlert(type, message) {
            const container = document.getElementById('recent-alerts');
            const alertDiv = document.createElement('div');
            alertDiv.className = `recent-alert alert-${type}`;
            
            const timestamp = new Date().toLocaleTimeString();
            alertDiv.innerHTML = `
                <div class="alert-content">${message}</div>
                <div class="alert-time">${timestamp}</div>
            `;
            
            container.insertBefore(alertDiv, container.firstChild);
            
            // 알림 수 제한
            const alerts = container.querySelectorAll('.recent-alert');
            if (alerts.length > 10) {
                alerts[alerts.length - 1].remove();
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>'''
    
    def _create_default_styles(self):
        """기본 CSS 스타일 생성"""
        css_content = '''/* TikBot 오버레이 스타일 */

body.overlay-body {
    margin: 0;
    padding: 0;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: transparent;
    color: #ffffff;
    overflow: hidden;
}

/* 오버레이 공통 스타일 */
.overlay-title {
    color: #00d4ff;
    margin: 0 0 15px 0;
    font-size: 20px;
    font-weight: bold;
    text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

/* 채팅 오버레이 */
.chat-container {
    background: rgba(0, 0, 0, 0.8);
    border-radius: 10px;
    padding: 15px;
    max-width: 400px;
    max-height: 500px;
    border: 2px solid #00d4ff;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

.chat-messages {
    height: 400px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: #00d4ff transparent;
}

.chat-messages::-webkit-scrollbar {
    width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
    background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
    background: #00d4ff;
    border-radius: 4px;
}

.chat-message {
    margin-bottom: 12px;
    padding: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    border-left: 3px solid #00d4ff;
}

.message-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
}

.username {
    font-weight: bold;
    color: #00d4ff;
}

.timestamp {
    font-size: 12px;
    color: #888;
}

.message-content {
    font-size: 14px;
    line-height: 1.4;
}

/* 통계 오버레이 */
.stats-container {
    background: rgba(0, 0, 0, 0.8);
    border-radius: 10px;
    padding: 15px;
    border: 2px solid #00d4ff;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
}

.stat-item {
    text-align: center;
    padding: 15px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    transition: all 0.3s ease;
}

.stat-item:hover {
    background: rgba(0, 212, 255, 0.2);
    transform: scale(1.05);
}

.stat-icon {
    font-size: 24px;
    margin-bottom: 8px;
}

.stat-value {
    font-size: 28px;
    font-weight: bold;
    color: #00d4ff;
    margin-bottom: 4px;
}

.stat-label {
    font-size: 12px;
    color: #ccc;
}

/* 목표 오버레이 */
.goal-container {
    background: rgba(0, 0, 0, 0.8);
    border-radius: 10px;
    padding: 15px;
    max-width: 350px;
    border: 2px solid #00d4ff;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

.goal-info {
    margin-bottom: 15px;
}

.goal-title {
    font-size: 18px;
    font-weight: bold;
    color: #00d4ff;
    margin-bottom: 5px;
}

.goal-description {
    font-size: 14px;
    color: #ccc;
}

.progress-container {
    margin-top: 15px;
}

.progress-bar {
    width: 100%;
    height: 20px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 8px;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #00d4ff, #0099cc);
    border-radius: 10px;
    transition: width 0.5s ease;
    position: relative;
}

.progress-fill.goal-completed {
    background: linear-gradient(90deg, #00ff88, #00cc66);
    animation: goalGlow 1s infinite alternate;
}

@keyframes goalGlow {
    from { box-shadow: 0 0 5px rgba(0, 255, 136, 0.5); }
    to { box-shadow: 0 0 20px rgba(0, 255, 136, 0.8); }
}

.progress-text {
    text-align: center;
    font-size: 14px;
    color: #ccc;
}

.goal-achieved {
    animation: goalAchieved 2s ease;
}

@keyframes goalAchieved {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

/* 알림 오버레이 */
.alerts-container {
    position: fixed;
    top: 20px;
    right: 20px;
    width: 350px;
    pointer-events: none;
}

.alert {
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 15px;
    margin-bottom: 10px;
    border-radius: 8px;
    border-left: 4px solid #00d4ff;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    transform: translateX(100%);
    opacity: 0;
    transition: all 0.5s ease;
}

.alert.alert-show {
    transform: translateX(0);
    opacity: 1;
}

.alert.alert-hide {
    transform: translateX(100%);
    opacity: 0;
}

.alert-follow {
    border-left-color: #ff6b6b;
}

.alert-gift {
    border-left-color: #ffd93d;
}

/* 최근 알림 (대시보드용) */
.recent-alert {
    padding: 10px;
    margin-bottom: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    border-left: 3px solid #00d4ff;
}

.recent-alert.alert-follow {
    border-left-color: #ff6b6b;
}

.recent-alert.alert-gift {
    border-left-color: #ffd93d;
}

.alert-content {
    font-size: 14px;
    margin-bottom: 4px;
}

.alert-time {
    font-size: 12px;
    color: #888;
}

/* 반응형 */
@media (max-width: 768px) {
    .stats-grid {
        grid-template-columns: 1fr;
    }
    
    .chat-container,
    .stats-container,
    .goal-container {
        max-width: 100%;
        margin: 10px;
    }
    
    .dashboard-grid {
        grid-template-columns: 1fr;
        grid-template-rows: repeat(4, auto);
    }
}'''
        
        css_path = self.static_dir / "css" / "overlay.css"
        if not css_path.exists():
            css_path.write_text(css_content, encoding='utf-8')
            self.logger.debug("기본 CSS 스타일 생성")
    
    def _create_default_scripts(self):
        """기본 JavaScript 파일 생성"""
        js_content = '''// TikBot 오버레이 WebSocket 클라이언트

class OverlayWebSocket {
    constructor(url) {
        this.url = url || 'ws://localhost:8080';
        this.socket = null;
        this.eventHandlers = {};
        this.reconnectInterval = 5000;
        this.maxReconnectAttempts = 10;
        this.reconnectAttempts = 0;
        this.isConnected = false;
        
        this.connect();
    }
    
    connect() {
        try {
            this.socket = new WebSocket(this.url);
            
            this.socket.onopen = () => {
                console.log('오버레이 WebSocket 연결됨');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                
                // 핑 전송 시작
                this.startPing();
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (e) {
                    console.error('메시지 파싱 오류:', e);
                }
            };
            
            this.socket.onclose = () => {
                console.log('오버레이 WebSocket 연결 종료');
                this.isConnected = false;
                this.attemptReconnect();
            };
            
            this.socket.onerror = (error) => {
                console.error('오버레이 WebSocket 오류:', error);
            };
            
        } catch (e) {
            console.error('WebSocket 연결 실패:', e);
            this.attemptReconnect();
        }
    }
    
    handleMessage(data) {
        const { type, data: eventData } = data;
        
        if (type === 'pong') {
            // 핑 응답 처리
            return;
        }
        
        // 이벤트 핸들러 호출
        if (this.eventHandlers[type]) {
            this.eventHandlers[type].forEach(handler => {
                try {
                    handler(eventData);
                } catch (e) {
                    console.error(`이벤트 핸들러 오류 (${type}):`, e);
                }
            });
        }
    }
    
    on(eventType, handler) {
        if (!this.eventHandlers[eventType]) {
            this.eventHandlers[eventType] = [];
        }
        this.eventHandlers[eventType].push(handler);
    }
    
    off(eventType, handler) {
        if (this.eventHandlers[eventType]) {
            const index = this.eventHandlers[eventType].indexOf(handler);
            if (index > -1) {
                this.eventHandlers[eventType].splice(index, 1);
            }
        }
    }
    
    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        }
    }
    
    requestData(dataType) {
        this.send({
            type: 'request_data',
            data_type: dataType
        });
    }
    
    startPing() {
        setInterval(() => {
            if (this.isConnected) {
                this.send({ type: 'ping' });
            }
        }, 30000); // 30초마다 핑
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectInterval);
        } else {
            console.error('최대 재연결 시도 횟수 초과');
        }
    }
    
    close() {
        if (this.socket) {
            this.socket.close();
        }
    }
}

// 유틸리티 함수들
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 전역에서 사용할 수 있도록 노출
window.OverlayWebSocket = OverlayWebSocket;
window.formatTime = formatTime;
window.formatNumber = formatNumber;
window.escapeHtml = escapeHtml;'''
        
        js_path = self.static_dir / "js" / "overlay-websocket.js"
        if not js_path.exists():
            js_path.write_text(js_content, encoding='utf-8')
            self.logger.debug("기본 JavaScript 파일 생성")
    
    def render_template(self, template_name: str, **context) -> str:
        """템플릿 렌더링"""
        try:
            template = self.jinja_env.get_template(f"overlay/{template_name}")
            return template.render(**context)
        except Exception as e:
            self.logger.error(f"템플릿 렌더링 실패 {template_name}: {e}")
            return f"<html><body><h1>템플릿 렌더링 오류</h1><p>{e}</p></body></html>"
    
    def get_overlay_urls(self, base_url: str = "http://localhost:8000") -> Dict[str, str]:
        """오버레이 URL 목록 반환"""
        return {
            "채팅 오버레이": f"{base_url}/overlay/chat",
            "통계 오버레이": f"{base_url}/overlay/stats", 
            "목표 오버레이": f"{base_url}/overlay/goal",
            "알림 오버레이": f"{base_url}/overlay/alerts",
            "통합 대시보드": f"{base_url}/overlay/dashboard"
        }
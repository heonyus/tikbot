// TikBot 오버레이 WebSocket 클라이언트

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
window.escapeHtml = escapeHtml;
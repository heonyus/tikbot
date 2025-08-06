"""
데이터 수집기 - 실시간 이벤트 데이터 수집 및 저장
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import sqlite3
import aiofiles
import os


class EventType(Enum):
    """이벤트 타입"""
    COMMENT = "comment"
    GIFT = "gift"
    FOLLOW = "follow"
    LIKE = "like"
    JOIN = "join"
    SHARE = "share"
    BOT_RESPONSE = "bot_response"
    MUSIC_REQUEST = "music_request"
    AI_INTERACTION = "ai_interaction"


@dataclass
class StreamEvent:
    """스트림 이벤트 데이터"""
    id: str
    event_type: EventType
    timestamp: datetime
    username: str
    nickname: str
    data: Dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "username": self.username,
            "nickname": self.nickname,
            "data": self.data,
            "session_id": self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamEvent':
        """딕셔너리에서 생성"""
        return cls(
            id=data["id"],
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            username=data["username"],
            nickname=data["nickname"],
            data=data.get("data", {}),
            session_id=data.get("session_id", "")
        )


@dataclass
class StreamSession:
    """방송 세션 정보"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    title: str = ""
    category: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "title": self.title,
            "category": self.category,
            "metadata": self.metadata
        }


class DataCollector:
    """실시간 데이터 수집기"""
    
    def __init__(self, 
                 data_dir: str = "data",
                 buffer_size: int = 100,
                 flush_interval: int = 60,
                 logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.data_dir = data_dir
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        # 현재 세션
        self.current_session: Optional[StreamSession] = None
        
        # 이벤트 버퍼
        self.event_buffer: List[StreamEvent] = []
        
        # 데이터베이스 연결
        self.db_path = os.path.join(data_dir, "analytics.db")
        self.db_connection: Optional[sqlite3.Connection] = None
        
        # 실시간 통계
        self.realtime_stats = {
            "events_collected": 0,
            "events_stored": 0,
            "last_flush_time": None,
            "buffer_usage": 0,
            "collection_rate": 0.0,  # events per minute
            "session_duration": 0
        }
        
        # 플러시 태스크
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def initialize(self) -> bool:
        """데이터 수집기 초기화"""
        try:
            # 데이터 디렉토리 생성
            os.makedirs(self.data_dir, exist_ok=True)
            
            # 데이터베이스 초기화
            await self._init_database()
            
            # 주기적 플러시 시작
            self._running = True
            self._flush_task = asyncio.create_task(self._periodic_flush())
            
            self.logger.info(f"📊 데이터 수집기 초기화 완료 - DB: {self.db_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"데이터 수집기 초기화 실패: {e}")
            return False
    
    async def _init_database(self):
        """데이터베이스 초기화"""
        self.db_connection = sqlite3.connect(self.db_path)
        cursor = self.db_connection.cursor()
        
        # 세션 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time TEXT NOT NULL,
                end_time TEXT,
                title TEXT,
                category TEXT,
                metadata TEXT
            )
        """)
        
        # 이벤트 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                username TEXT NOT NULL,
                nickname TEXT NOT NULL,
                data TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        """)
        
        # 인덱스 생성
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_timestamp 
            ON events (timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_type 
            ON events (event_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_username 
            ON events (username)
        """)
        
        self.db_connection.commit()
    
    async def start_session(self, title: str = "", category: str = "", 
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """새 방송 세션 시작"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = StreamSession(
            session_id=session_id,
            start_time=datetime.now(),
            title=title,
            category=category,
            metadata=metadata or {}
        )
        
        # 데이터베이스에 세션 저장
        if self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, start_time, title, category, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                self.current_session.start_time.isoformat(),
                title,
                category,
                json.dumps(metadata or {})
            ))
            self.db_connection.commit()
        
        self.logger.info(f"📊 새 방송 세션 시작: {session_id}")
        return session_id
    
    async def end_session(self):
        """현재 방송 세션 종료"""
        if not self.current_session:
            return
        
        self.current_session.end_time = datetime.now()
        
        # 데이터베이스 업데이트
        if self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                UPDATE sessions SET end_time = ? WHERE session_id = ?
            """, (
                self.current_session.end_time.isoformat(),
                self.current_session.session_id
            ))
            self.db_connection.commit()
        
        # 버퍼 플러시
        await self._flush_buffer()
        
        session_duration = (self.current_session.end_time - self.current_session.start_time).total_seconds()
        self.logger.info(f"📊 방송 세션 종료: {self.current_session.session_id} (지속시간: {session_duration:.0f}초)")
        
        self.current_session = None
    
    async def collect_event(self, event_type: EventType, username: str, 
                           nickname: str, data: Optional[Dict[str, Any]] = None):
        """이벤트 수집"""
        if not self.current_session:
            # 세션이 없으면 자동으로 시작
            await self.start_session()
        
        event = StreamEvent(
            id=f"{event_type.value}_{datetime.now().timestamp()}",
            event_type=event_type,
            timestamp=datetime.now(),
            username=username,
            nickname=nickname,
            data=data or {},
            session_id=self.current_session.session_id
        )
        
        # 버퍼에 추가
        self.event_buffer.append(event)
        self.realtime_stats["events_collected"] += 1
        self.realtime_stats["buffer_usage"] = len(self.event_buffer)
        
        # 버퍼가 가득 차면 플러시
        if len(self.event_buffer) >= self.buffer_size:
            await self._flush_buffer()
    
    async def _flush_buffer(self):
        """버퍼를 데이터베이스에 플러시"""
        if not self.event_buffer or not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            
            # 배치 삽입
            events_data = []
            for event in self.event_buffer:
                events_data.append((
                    event.id,
                    event.session_id,
                    event.event_type.value,
                    event.timestamp.isoformat(),
                    event.username,
                    event.nickname,
                    json.dumps(event.data)
                ))
            
            cursor.executemany("""
                INSERT OR REPLACE INTO events 
                (id, session_id, event_type, timestamp, username, nickname, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, events_data)
            
            self.db_connection.commit()
            
            # 통계 업데이트
            events_stored = len(self.event_buffer)
            self.realtime_stats["events_stored"] += events_stored
            self.realtime_stats["last_flush_time"] = datetime.now().isoformat()
            
            self.logger.debug(f"📊 이벤트 {events_stored}개 데이터베이스에 저장")
            
            # 버퍼 클리어
            self.event_buffer.clear()
            self.realtime_stats["buffer_usage"] = 0
            
        except Exception as e:
            self.logger.error(f"버퍼 플러시 실패: {e}")
    
    async def _periodic_flush(self):
        """주기적 버퍼 플러시"""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_buffer()
                
                # 수집률 계산 (분당 이벤트 수)
                if self.current_session:
                    duration_minutes = (datetime.now() - self.current_session.start_time).total_seconds() / 60
                    if duration_minutes > 0:
                        self.realtime_stats["collection_rate"] = self.realtime_stats["events_collected"] / duration_minutes
                        self.realtime_stats["session_duration"] = duration_minutes * 60
                
            except Exception as e:
                self.logger.error(f"주기적 플러시 실패: {e}")
    
    async def get_events(self, 
                        session_id: Optional[str] = None,
                        event_types: Optional[List[EventType]] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        username: Optional[str] = None,
                        limit: int = 1000) -> List[StreamEvent]:
        """이벤트 조회"""
        if not self.db_connection:
            return []
        
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        if event_types:
            placeholders = ",".join("?" * len(event_types))
            query += f" AND event_type IN ({placeholders})"
            params.extend([et.value for et in event_types])
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        if username:
            query += " AND username = ?"
            params.append(username)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = self.db_connection.cursor()
        cursor.execute(query, params)
        
        events = []
        for row in cursor.fetchall():
            events.append(StreamEvent(
                id=row[0],
                event_type=EventType(row[2]),
                timestamp=datetime.fromisoformat(row[3]),
                username=row[4],
                nickname=row[5],
                data=json.loads(row[6] or "{}"),
                session_id=row[1]
            ))
        
        return events
    
    async def get_sessions(self, limit: int = 50) -> List[StreamSession]:
        """세션 목록 조회"""
        if not self.db_connection:
            return []
        
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT * FROM sessions 
            ORDER BY start_time DESC 
            LIMIT ?
        """, (limit,))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append(StreamSession(
                session_id=row[0],
                start_time=datetime.fromisoformat(row[1]),
                end_time=datetime.fromisoformat(row[2]) if row[2] else None,
                title=row[3] or "",
                category=row[4] or "",
                metadata=json.loads(row[5] or "{}")
            ))
        
        return sessions
    
    async def get_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """통계 조회"""
        if not self.db_connection:
            return {}
        
        cursor = self.db_connection.cursor()
        
        # 기본 조건
        where_clause = ""
        params = []
        if session_id:
            where_clause = "WHERE session_id = ?"
            params.append(session_id)
        
        # 이벤트 타입별 카운트
        cursor.execute(f"""
            SELECT event_type, COUNT(*) 
            FROM events {where_clause}
            GROUP BY event_type
        """, params)
        
        event_counts = dict(cursor.fetchall())
        
        # 사용자별 활동
        cursor.execute(f"""
            SELECT username, nickname, COUNT(*) as activity_count
            FROM events {where_clause}
            GROUP BY username, nickname
            ORDER BY activity_count DESC
            LIMIT 10
        """, params)
        
        top_users = [
            {"username": row[0], "nickname": row[1], "activity_count": row[2]}
            for row in cursor.fetchall()
        ]
        
        # 시간대별 활동 (시간별)
        cursor.execute(f"""
            SELECT strftime('%H', timestamp) as hour, COUNT(*) 
            FROM events {where_clause}
            GROUP BY hour
            ORDER BY hour
        """, params)
        
        hourly_activity = dict(cursor.fetchall())
        
        return {
            "event_counts": event_counts,
            "top_users": top_users,
            "hourly_activity": hourly_activity,
            "realtime_stats": self.realtime_stats
        }
    
    async def export_data(self, 
                         session_id: Optional[str] = None,
                         format: str = "json") -> str:
        """데이터 내보내기"""
        events = await self.get_events(session_id=session_id, limit=10000)
        
        if format == "json":
            data = {
                "session_id": session_id,
                "export_time": datetime.now().isoformat(),
                "events": [event.to_dict() for event in events],
                "statistics": await self.get_statistics(session_id)
            }
            
            filename = f"export_{session_id or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.data_dir, filename)
            
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            
            return filepath
        
        # CSV 형식도 추가 가능
        raise NotImplementedError(f"Export format '{format}' not supported")
    
    def get_realtime_stats(self) -> Dict[str, Any]:
        """실시간 통계 반환"""
        return self.realtime_stats.copy()
    
    async def cleanup(self):
        """리소스 정리"""
        self._running = False
        
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # 최종 플러시
        await self._flush_buffer()
        
        # 현재 세션 종료
        if self.current_session:
            await self.end_session()
        
        # 데이터베이스 연결 종료
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None
        
        self.logger.info("📊 데이터 수집기 정리 완료")
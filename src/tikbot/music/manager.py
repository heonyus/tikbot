"""
Music Manager - Spotify + YouTube 통합 관리
"""

import asyncio
import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime

from .queue import MusicQueue, MusicRequest
from .spotify import SpotifyIntegration
from .youtube import YouTubeIntegration
from ..core.events import EventHandler, EventType, Event


class MusicManager:
    """음악 통합 매니저"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.enabled = config.get('enabled', True)
        self.event_handler: Optional[EventHandler] = None
        
        # 컴포넌트들
        self.queue = MusicQueue(
            max_queue_size=config.get('max_queue_size', 50),
            max_duration=config.get('max_duration', 600),
            logger=self.logger
        )
        
        self.spotify: Optional[SpotifyIntegration] = None
        self.youtube: Optional[YouTubeIntegration] = None
        
        # 설정
        self.auto_play = config.get('auto_play', True)
        self.allow_explicit = config.get('allow_explicit', False)
        self.admin_users = set(config.get('admin_users', []))
        
        # 현재 재생 상태
        self.is_playing = False
        self.current_position = 0
        
        # 통계
        self.stats = {
            "initialization_time": None,
            "total_requests": 0,
            "spotify_requests": 0,
            "youtube_requests": 0,
            "songs_played": 0,
            "songs_skipped": 0
        }
    
    async def initialize(self) -> bool:
        """음악 시스템 초기화"""
        if not self.enabled:
            self.logger.info("음악 시스템이 비활성화되어 있습니다.")
            return True
        
        try:
            import time
            start_time = time.time()
            
            # Spotify 초기화
            spotify_config = self.config.get('spotify', {})
            if spotify_config.get('enabled', True):
                self.spotify = SpotifyIntegration(
                    client_id=spotify_config.get('client_id'),
                    client_secret=spotify_config.get('client_secret'),
                    logger=self.logger
                )
                
                if not await self.spotify.initialize():
                    self.logger.warning("Spotify 초기화 실패")
                    self.spotify = None
            
            # YouTube 초기화
            youtube_config = self.config.get('youtube', {})
            if youtube_config.get('enabled', True):
                self.youtube = YouTubeIntegration(logger=self.logger)
                
                if not self.youtube.is_available():
                    self.logger.warning("YouTube 초기화 실패")
                    self.youtube = None
            
            # 큐 설정 업데이트
            queue_settings = {
                "blocked_keywords": self.config.get('blocked_keywords', []),
                "max_requests_per_user": self.config.get('max_requests_per_user', 3)
            }
            self.queue.update_settings(queue_settings)
            
            # 초기화 시간 기록
            self.stats["initialization_time"] = time.time() - start_time
            
            # 사용 가능한 플랫폼 확인
            available_platforms = []
            if self.spotify and self.spotify.is_available():
                available_platforms.append("Spotify")
            if self.youtube and self.youtube.is_available():
                available_platforms.append("YouTube")
            
            if available_platforms:
                self.logger.info(f"🎵 음악 시스템 초기화 완료 - 플랫폼: {', '.join(available_platforms)}")
            else:
                self.logger.warning("사용 가능한 음악 플랫폼이 없습니다.")
            
            return True
            
        except Exception as e:
            self.logger.error(f"음악 시스템 초기화 실패: {e}")
            return False
    
    def register_event_handlers(self, event_handler: EventHandler):
        """이벤트 핸들러에 음악 이벤트 등록"""
        if not self.enabled:
            return
        
        self.event_handler = event_handler
        
        @event_handler.on(EventType.COMMAND)
        async def on_music_command(event_data):
            command = event_data.get("command", "").lower()
            username = event_data.get("username", "")
            nickname = event_data.get("nickname", username)
            args = event_data.get("args", [])
            
            # 음악 요청 명령어
            if command in ["!music", "!song", "!play"]:
                if args:
                    query = " ".join(args)
                    result = await self.request_song(query, username, nickname)
                    # 결과를 채팅으로 알림 (오버레이 또는 채팅으로)
                    if result["success"]:
                        self.logger.info(f"🎵 {nickname}: {result['message']}")
                    else:
                        self.logger.warning(f"🎵 {nickname}: {result['error']}")
            
            # 큐 조회
            elif command == "!queue":
                queue_info = self.get_queue_info()
                if queue_info["current"]:
                    current = queue_info["current"]
                    self.logger.info(f"🎵 현재 재생: {current['title']} - {current['artist']}")
                
                if queue_info["queue"]:
                    next_songs = queue_info["queue"][:3]  # 다음 3곡
                    for i, song in enumerate(next_songs, 1):
                        self.logger.info(f"🎵 {i}. {song['title']} - {song['artist']}")
            
            # 스킵 (관리자 또는 요청자)
            elif command == "!skip":
                if username in self.admin_users:
                    result = await self.skip_current_song("관리자 요청")
                    if result:
                        self.logger.info(f"🎵 관리자가 곡을 스킵했습니다")
                else:
                    # 일반 사용자는 자신이 요청한 곡만 스킵 가능
                    current = self.queue.current_request
                    if current and current.requester == username:
                        result = await self.skip_current_song("요청자 스킵")
                        if result:
                            self.logger.info(f"🎵 요청자가 곡을 스킵했습니다")
            
            # 큐 비우기 (관리자만)
            elif command == "!clearqueue" and username in self.admin_users:
                result = self.queue.clear_queue(admin=True)
                if result:
                    self.logger.info("🎵 관리자가 음악 큐를 비웠습니다")
        
        self.logger.info("음악 이벤트 핸들러 등록 완료")
    
    async def request_song(self, query: str, requester: str, requester_nickname: str) -> Dict[str, Any]:
        """음악 요청 처리"""
        if not self.enabled:
            return {"success": False, "error": "음악 시스템이 비활성화되어 있습니다"}
        
        self.stats["total_requests"] += 1
        
        try:
            # URL인지 검색어인지 판단
            if self._is_url(query):
                result = await self._handle_url_request(query, requester, requester_nickname)
            else:
                result = await self._handle_search_request(query, requester, requester_nickname)
            
            if result["success"]:
                # 통계 업데이트
                if result.get("platform") == "spotify":
                    self.stats["spotify_requests"] += 1
                elif result.get("platform") == "youtube":
                    self.stats["youtube_requests"] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"음악 요청 처리 실패: {e}")
            return {"success": False, "error": "음악 요청 처리 중 오류가 발생했습니다"}
    
    async def _handle_url_request(self, url: str, requester: str, requester_nickname: str) -> Dict[str, Any]:
        """URL 기반 음악 요청 처리"""
        # Spotify URL
        if "spotify.com" in url and self.spotify:
            track_info = await self.spotify.get_track_by_url(url)
            if track_info:
                # 성인 콘텐츠 필터
                if track_info.get("explicit") and not self.allow_explicit:
                    return {"success": False, "error": "성인 콘텐츠는 허용되지 않습니다"}
                
                music_request = await self.spotify.create_music_request(
                    track_info, requester, requester_nickname
                )
                
                result = await self.queue.add_request(music_request)
                result["platform"] = "spotify"
                
                # 음악 요청 추가 이벤트 발생
                if result["success"] and self.event_handler:
                    await self.event_handler.emit(Event(
                        EventType.MUSIC_REQUEST_ADDED,
                        music_request.to_dict()
                    ))
                
                return result
            else:
                return {"success": False, "error": "Spotify 트랙을 찾을 수 없습니다"}
        
        # YouTube URL
        elif self.youtube and self.youtube.is_youtube_url(url):
            video_info = await self.youtube.get_video_info(url)
            if video_info:
                music_request = await self.youtube.create_music_request(
                    video_info, requester, requester_nickname
                )
                
                result = await self.queue.add_request(music_request)
                result["platform"] = "youtube"
                
                # 음악 요청 추가 이벤트 발생
                if result["success"] and self.event_handler:
                    await self.event_handler.emit(Event(
                        EventType.MUSIC_REQUEST_ADDED,
                        music_request.to_dict()
                    ))
                
                return result
            else:
                return {"success": False, "error": "YouTube 비디오를 찾을 수 없습니다"}
        
        else:
            return {"success": False, "error": "지원하지 않는 URL입니다"}
    
    async def _handle_search_request(self, query: str, requester: str, requester_nickname: str) -> Dict[str, Any]:
        """검색어 기반 음악 요청 처리"""
        # Spotify 우선 검색
        if self.spotify:
            tracks = await self.spotify.search_track(query, limit=1)
            if tracks:
                track_info = tracks[0]
                
                # 성인 콘텐츠 필터
                if track_info.get("explicit") and not self.allow_explicit:
                    # YouTube에서 대체 검색
                    if self.youtube:
                        return await self._search_youtube_fallback(query, requester, requester_nickname)
                    else:
                        return {"success": False, "error": "성인 콘텐츠는 허용되지 않습니다"}
                
                music_request = await self.spotify.create_music_request(
                    track_info, requester, requester_nickname
                )
                
                result = await self.queue.add_request(music_request)
                result["platform"] = "spotify"
                
                # 음악 요청 추가 이벤트 발생
                if result["success"] and self.event_handler:
                    await self.event_handler.emit(Event(
                        EventType.MUSIC_REQUEST_ADDED,
                        music_request.to_dict()
                    ))
                
                return result
        
        # Spotify가 없거나 결과가 없으면 YouTube 검색
        if self.youtube:
            return await self._search_youtube_fallback(query, requester, requester_nickname)
        
        return {"success": False, "error": "사용 가능한 음악 플랫폼이 없습니다"}
    
    async def _search_youtube_fallback(self, query: str, requester: str, requester_nickname: str) -> Dict[str, Any]:
        """YouTube 대체 검색"""
        videos = await self.youtube.search_videos(query, limit=1)
        if videos:
            video_info = videos[0]
            music_request = await self.youtube.create_music_request(
                video_info, requester, requester_nickname
            )
            
            result = await self.queue.add_request(music_request)
            result["platform"] = "youtube"
            
            # 음악 요청 추가 이벤트 발생
            if result["success"] and self.event_handler:
                await self.event_handler.emit(Event(
                    EventType.MUSIC_REQUEST_ADDED,
                    music_request.to_dict()
                ))
            
            return result
        else:
            return {"success": False, "error": "음악을 찾을 수 없습니다"}
    
    def _is_url(self, text: str) -> bool:
        """URL 여부 확인"""
        url_patterns = [
            r"https?://",
            r"spotify\.com",
            r"youtu\.be",
            r"youtube\.com"
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in url_patterns)
    
    async def skip_current_song(self, reason: str = "사용자 요청") -> bool:
        """현재 곡 스킵"""
        result = await self.queue.skip_current(reason)
        if result:
            self.stats["songs_skipped"] += 1
            
            # 자동 재생이 활성화된 경우 다음 곡 재생
            if self.auto_play:
                await self._play_next_song()
        
        return result
    
    async def _play_next_song(self):
        """다음 곡 자동 재생"""
        next_request = await self.queue.get_next_request()
        if next_request:
            self.is_playing = True
            self.current_position = 0
            self.stats["songs_played"] += 1
            
            self.logger.info(f"🎵 재생 시작: {next_request.title} - {next_request.artist}")
            
            # 음악 재생 시작 이벤트 발생
            if self.event_handler:
                await self.event_handler.emit(Event(
                    EventType.MUSIC_SONG_STARTED,
                    next_request.to_dict()
                ))
            
            # 실제 음악 재생은 외부 플레이어에서 처리
            # 여기서는 재생 상태만 관리
    
    def get_queue_info(self) -> Dict[str, Any]:
        """큐 정보 반환"""
        return self.queue.get_queue_info()
    
    def get_user_requests(self, username: str) -> List[Dict[str, Any]]:
        """사용자 요청 목록"""
        return self.queue.get_user_requests(username)
    
    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """재생 히스토리"""
        return self.queue.get_history(limit)
    
    async def search_music(self, query: str, platform: str = "auto", limit: int = 10) -> List[Dict[str, Any]]:
        """음악 검색 (UI용)"""
        results = []
        
        if platform in ["auto", "spotify"] and self.spotify:
            spotify_results = await self.spotify.search_track(query, limit=limit//2 if platform == "auto" else limit)
            results.extend(spotify_results)
        
        if platform in ["auto", "youtube"] and self.youtube:
            youtube_results = await self.youtube.search_videos(query, limit=limit//2 if platform == "auto" else limit)
            results.extend(youtube_results)
        
        return results
    
    def add_admin_user(self, username: str):
        """관리자 사용자 추가"""
        self.admin_users.add(username)
    
    def remove_admin_user(self, username: str):
        """관리자 사용자 제거"""
        self.admin_users.discard(username)
    
    def update_settings(self, settings: Dict[str, Any]):
        """설정 업데이트"""
        if "auto_play" in settings:
            self.auto_play = settings["auto_play"]
        
        if "allow_explicit" in settings:
            self.allow_explicit = settings["allow_explicit"]
        
        if "admin_users" in settings:
            self.admin_users = set(settings["admin_users"])
        
        # 큐 설정도 업데이트
        queue_settings = {}
        for key in ["max_queue_size", "max_duration", "max_requests_per_user", "blocked_keywords"]:
            if key in settings:
                queue_settings[key] = settings[key]
        
        if queue_settings:
            self.queue.update_settings(queue_settings)
    
    def get_stats(self) -> Dict[str, Any]:
        """통합 통계 반환"""
        stats = self.stats.copy()
        
        # 큐 통계 추가
        queue_stats = self.queue.get_stats()
        stats.update({f"queue_{k}": v for k, v in queue_stats.items()})
        
        # 플랫폼별 통계 추가
        if self.spotify:
            spotify_stats = self.spotify.get_stats()
            stats.update({f"spotify_{k}": v for k, v in spotify_stats.items()})
        
        if self.youtube:
            youtube_stats = self.youtube.get_stats()
            stats.update({f"youtube_{k}": v for k, v in youtube_stats.items()})
        
        stats.update({
            "enabled": self.enabled,
            "platforms_available": {
                "spotify": self.spotify is not None and self.spotify.is_available(),
                "youtube": self.youtube is not None and self.youtube.is_available()
            },
            "is_playing": self.is_playing,
            "auto_play": self.auto_play
        })
        
        return stats
    
    async def cleanup(self):
        """리소스 정리"""
        self.is_playing = False
        self.queue.clear_queue(admin=True)
        
        self.logger.info("음악 매니저 정리 완료")
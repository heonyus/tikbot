"""
Spotify 통합 모듈
"""

import asyncio
import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    SPOTIPY_AVAILABLE = True
except ImportError:
    SPOTIPY_AVAILABLE = False

from .queue import MusicRequest, RequestStatus


class SpotifyIntegration:
    """Spotify API 통합"""
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.client_id = client_id
        self.client_secret = client_secret
        self.spotify: Optional[spotipy.Spotify] = None
        
        # 캐시
        self.search_cache = {}
        self.track_cache = {}
        
        # 통계
        self.stats = {
            "api_calls": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "cache_hits": 0
        }
        
        if not SPOTIPY_AVAILABLE:
            self.logger.warning("spotipy 라이브러리가 설치되지 않았습니다.")
    
    async def initialize(self) -> bool:
        """Spotify API 초기화"""
        if not SPOTIPY_AVAILABLE:
            self.logger.error("spotipy를 사용할 수 없습니다.")
            return False
        
        if not self.client_id or not self.client_secret:
            self.logger.warning("Spotify API 키가 설정되지 않았습니다.")
            return False
        
        try:
            client_credentials_manager = SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            self.spotify = spotipy.Spotify(
                client_credentials_manager=client_credentials_manager
            )
            
            # 연결 테스트
            await self._test_connection()
            
            self.logger.info("🎵 Spotify API 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"Spotify API 초기화 실패: {e}")
            return False
    
    async def _test_connection(self):
        """연결 테스트"""
        def _test():
            # 간단한 검색으로 연결 테스트
            results = self.spotify.search(q="test", type="track", limit=1)
            return len(results["tracks"]["items"]) >= 0
        
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(None, _test)
        
        if not success:
            raise Exception("Spotify API 연결 테스트 실패")
    
    async def search_track(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """트랙 검색"""
        if not self.spotify:
            return []
        
        # 캐시 확인
        cache_key = hashlib.md5(f"{query}_{limit}".encode()).hexdigest()
        if cache_key in self.search_cache:
            self.stats["cache_hits"] += 1
            return self.search_cache[cache_key]
        
        try:
            def _search():
                self.stats["api_calls"] += 1
                return self.spotify.search(q=query, type="track", limit=limit)
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, _search)
            
            tracks = []
            for track in results["tracks"]["items"]:
                track_info = self._format_track_info(track)
                tracks.append(track_info)
            
            # 캐시 저장 (최대 100개)
            if len(self.search_cache) < 100:
                self.search_cache[cache_key] = tracks
            
            self.stats["successful_searches"] += 1
            return tracks
            
        except Exception as e:
            self.logger.error(f"Spotify 검색 실패: {e}")
            self.stats["failed_searches"] += 1
            return []
    
    async def get_track_by_url(self, spotify_url: str) -> Optional[Dict[str, Any]]:
        """Spotify URL로 트랙 정보 가져오기"""
        if not self.spotify:
            return None
        
        # URL에서 트랙 ID 추출
        track_id = self._extract_track_id(spotify_url)
        if not track_id:
            return None
        
        # 캐시 확인
        if track_id in self.track_cache:
            self.stats["cache_hits"] += 1
            return self.track_cache[track_id]
        
        try:
            def _get_track():
                self.stats["api_calls"] += 1
                return self.spotify.track(track_id)
            
            loop = asyncio.get_event_loop()
            track = await loop.run_in_executor(None, _get_track)
            
            track_info = self._format_track_info(track)
            
            # 캐시 저장
            if len(self.track_cache) < 100:
                self.track_cache[track_id] = track_info
            
            return track_info
            
        except Exception as e:
            self.logger.error(f"Spotify 트랙 조회 실패: {e}")
            return None
    
    def _extract_track_id(self, spotify_url: str) -> Optional[str]:
        """Spotify URL에서 트랙 ID 추출"""
        patterns = [
            r"spotify:track:([a-zA-Z0-9]{22})",
            r"open\.spotify\.com/track/([a-zA-Z0-9]{22})",
            r"spotify\.com/track/([a-zA-Z0-9]{22})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, spotify_url)
            if match:
                return match.group(1)
        
        return None
    
    def _format_track_info(self, track: Dict[str, Any]) -> Dict[str, Any]:
        """Spotify 트랙 정보를 표준 형식으로 변환"""
        artists = ", ".join([artist["name"] for artist in track["artists"]])
        
        # 썸네일 이미지
        thumbnail = None
        if track["album"]["images"]:
            thumbnail = track["album"]["images"][0]["url"]
        
        return {
            "id": track["id"],
            "title": track["name"],
            "artist": artists,
            "album": track["album"]["name"],
            "duration": track["duration_ms"] // 1000,  # 밀리초를 초로 변환
            "url": track["external_urls"]["spotify"],
            "thumbnail": thumbnail,
            "explicit": track["explicit"],
            "popularity": track["popularity"],
            "platform": "spotify",
            "release_date": track["album"]["release_date"],
            "preview_url": track["preview_url"]
        }
    
    async def create_music_request(self, track_info: Dict[str, Any], 
                                 requester: str, requester_nickname: str) -> MusicRequest:
        """Spotify 트랙 정보로 MusicRequest 생성"""
        request_id = hashlib.md5(
            f"spotify_{track_info['id']}_{requester}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        return MusicRequest(
            id=request_id,
            title=track_info["title"],
            artist=track_info["artist"],
            duration=track_info["duration"],
            platform="spotify",
            url=track_info["url"],
            requester=requester,
            requester_nickname=requester_nickname,
            timestamp=datetime.now(),
            album=track_info.get("album"),
            thumbnail=track_info.get("thumbnail"),
            explicit=track_info.get("explicit", False)
        )
    
    async def get_recommendations(self, seed_track_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """추천 트랙 가져오기"""
        if not self.spotify:
            return []
        
        try:
            def _get_recommendations():
                self.stats["api_calls"] += 1
                return self.spotify.recommendations(
                    seed_tracks=[seed_track_id],
                    limit=limit
                )
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, _get_recommendations)
            
            recommendations = []
            for track in results["tracks"]:
                track_info = self._format_track_info(track)
                recommendations.append(track_info)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Spotify 추천 조회 실패: {e}")
            return []
    
    async def get_playlist_tracks(self, playlist_url: str, limit: int = 50) -> List[Dict[str, Any]]:
        """플레이리스트 트랙 목록 가져오기"""
        if not self.spotify:
            return []
        
        playlist_id = self._extract_playlist_id(playlist_url)
        if not playlist_id:
            return []
        
        try:
            def _get_playlist():
                self.stats["api_calls"] += 1
                return self.spotify.playlist_tracks(playlist_id, limit=limit)
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, _get_playlist)
            
            tracks = []
            for item in results["items"]:
                if item["track"] and item["track"]["type"] == "track":
                    track_info = self._format_track_info(item["track"])
                    tracks.append(track_info)
            
            return tracks
            
        except Exception as e:
            self.logger.error(f"Spotify 플레이리스트 조회 실패: {e}")
            return []
    
    def _extract_playlist_id(self, playlist_url: str) -> Optional[str]:
        """Spotify 플레이리스트 URL에서 ID 추출"""
        patterns = [
            r"spotify:playlist:([a-zA-Z0-9]{22})",
            r"open\.spotify\.com/playlist/([a-zA-Z0-9]{22})",
            r"spotify\.com/playlist/([a-zA-Z0-9]{22})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, playlist_url)
            if match:
                return match.group(1)
        
        return None
    
    def is_available(self) -> bool:
        """Spotify 사용 가능 여부"""
        return SPOTIPY_AVAILABLE and self.spotify is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        cache_hit_rate = 0
        if self.stats["api_calls"] > 0:
            cache_hit_rate = self.stats["cache_hits"] / (self.stats["api_calls"] + self.stats["cache_hits"])
        
        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "search_cache_size": len(self.search_cache),
            "track_cache_size": len(self.track_cache),
            "available": self.is_available()
        }
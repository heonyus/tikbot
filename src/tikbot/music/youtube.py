"""
YouTube 통합 모듈
"""

import asyncio
import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib

try:
    import youtube_dl
    YOUTUBE_DL_AVAILABLE = True
except ImportError:
    try:
        import yt_dlp as youtube_dl
        YOUTUBE_DL_AVAILABLE = True
    except ImportError:
        YOUTUBE_DL_AVAILABLE = False

try:
    from youtubesearchpython import VideosSearch, Video
    YOUTUBE_SEARCH_AVAILABLE = True
except ImportError:
    YOUTUBE_SEARCH_AVAILABLE = False

from .queue import MusicRequest, RequestStatus


class YouTubeIntegration:
    """YouTube API 통합"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # YouTube DL 설정
        self.ytdl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'format': 'bestaudio/best',
        }
        
        # 캐시
        self.search_cache = {}
        self.video_cache = {}
        
        # 통계
        self.stats = {
            "searches": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "cache_hits": 0
        }
        
        if not YOUTUBE_DL_AVAILABLE:
            self.logger.warning("youtube-dl 또는 yt-dlp가 설치되지 않았습니다.")
        
        if not YOUTUBE_SEARCH_AVAILABLE:
            self.logger.warning("youtube-search-python이 설치되지 않았습니다.")
    
    async def search_videos(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """YouTube 비디오 검색"""
        if not YOUTUBE_SEARCH_AVAILABLE:
            return []
        
        # 캐시 확인
        cache_key = hashlib.md5(f"{query}_{limit}".encode()).hexdigest()
        if cache_key in self.search_cache:
            self.stats["cache_hits"] += 1
            return self.search_cache[cache_key]
        
        try:
            def _search():
                self.stats["searches"] += 1
                videos_search = VideosSearch(query, limit=limit)
                return videos_search.result()
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, _search)
            
            videos = []
            for video in results["result"]:
                video_info = self._format_video_info(video)
                if video_info:
                    videos.append(video_info)
            
            # 캐시 저장 (최대 100개)
            if len(self.search_cache) < 100:
                self.search_cache[cache_key] = videos
            
            return videos
            
        except Exception as e:
            self.logger.error(f"YouTube 검색 실패: {e}")
            return []
    
    async def get_video_info(self, video_url: str) -> Optional[Dict[str, Any]]:
        """YouTube URL로 비디오 정보 가져오기"""
        if not YOUTUBE_DL_AVAILABLE:
            return None
        
        # URL에서 비디오 ID 추출
        video_id = self._extract_video_id(video_url)
        if not video_id:
            return None
        
        # 캐시 확인
        if video_id in self.video_cache:
            self.stats["cache_hits"] += 1
            return self.video_cache[video_id]
        
        try:
            def _extract_info():
                with youtube_dl.YoutubeDL(self.ytdl_opts) as ydl:
                    return ydl.extract_info(video_url, download=False)
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, _extract_info)
            
            video_info = self._format_video_info_from_ytdl(info)
            
            # 캐시 저장
            if len(self.video_cache) < 100:
                self.video_cache[video_id] = video_info
            
            self.stats["successful_extractions"] += 1
            return video_info
            
        except Exception as e:
            self.logger.error(f"YouTube 비디오 정보 추출 실패: {e}")
            self.stats["failed_extractions"] += 1
            return None
    
    def _extract_video_id(self, video_url: str) -> Optional[str]:
        """YouTube URL에서 비디오 ID 추출"""
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
            r"youtube\.com/v/([a-zA-Z0-9_-]{11})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                return match.group(1)
        
        return None
    
    def _format_video_info(self, video: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """YouTube 검색 결과를 표준 형식으로 변환"""
        try:
            # 시간 파싱
            duration_str = video.get("duration")
            duration = self._parse_duration(duration_str) if duration_str else 0
            
            # 너무 긴 비디오 필터링 (10분 이상)
            if duration > 600:
                return None
            
            return {
                "id": video["id"],
                "title": video["title"],
                "artist": video["channel"]["name"],
                "album": None,
                "duration": duration,
                "url": video["link"],
                "thumbnail": video["thumbnails"][0]["url"] if video["thumbnails"] else None,
                "explicit": False,
                "platform": "youtube",
                "view_count": self._parse_view_count(video.get("viewCount", {}).get("text", "0")),
                "upload_date": video.get("publishedTime", ""),
                "description": video.get("descriptionSnippet", [{}])[0].get("text", "")[:200]
            }
        except Exception as e:
            self.logger.error(f"비디오 정보 포맷팅 실패: {e}")
            return None
    
    def _format_video_info_from_ytdl(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """youtube-dl 결과를 표준 형식으로 변환"""
        # 업로더 정보
        uploader = info.get("uploader", info.get("channel", "Unknown"))
        
        return {
            "id": info["id"],
            "title": info["title"],
            "artist": uploader,
            "album": None,
            "duration": info.get("duration", 0),
            "url": info["webpage_url"],
            "thumbnail": info.get("thumbnail"),
            "explicit": False,
            "platform": "youtube",
            "view_count": info.get("view_count", 0),
            "upload_date": info.get("upload_date", ""),
            "description": info.get("description", "")[:200]
        }
    
    def _parse_duration(self, duration_str: str) -> int:
        """YouTube 시간 형식을 초로 변환"""
        try:
            # "5:23" 형식 파싱
            if ":" in duration_str:
                parts = duration_str.split(":")
                if len(parts) == 2:
                    minutes, seconds = parts
                    return int(minutes) * 60 + int(seconds)
                elif len(parts) == 3:
                    hours, minutes, seconds = parts
                    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        except:
            pass
        
        return 0
    
    def _parse_view_count(self, view_count_str: str) -> int:
        """조회수 문자열을 숫자로 변환"""
        try:
            # "1,234,567 views" 형식에서 숫자만 추출
            import re
            numbers = re.findall(r'[\d,]+', view_count_str)
            if numbers:
                return int(numbers[0].replace(',', ''))
        except:
            pass
        
        return 0
    
    async def create_music_request(self, video_info: Dict[str, Any], 
                                 requester: str, requester_nickname: str) -> MusicRequest:
        """YouTube 비디오 정보로 MusicRequest 생성"""
        request_id = hashlib.md5(
            f"youtube_{video_info['id']}_{requester}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        return MusicRequest(
            id=request_id,
            title=video_info["title"],
            artist=video_info["artist"],
            duration=video_info["duration"],
            platform="youtube",
            url=video_info["url"],
            requester=requester,
            requester_nickname=requester_nickname,
            timestamp=datetime.now(),
            thumbnail=video_info.get("thumbnail"),
            explicit=False
        )
    
    async def get_related_videos(self, video_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """관련 비디오 가져오기"""
        if not YOUTUBE_SEARCH_AVAILABLE:
            return []
        
        try:
            def _get_related():
                video = Video.getInfo(video_id)
                if "title" in video:
                    # 제목을 기반으로 관련 비디오 검색
                    search_query = video["title"]["simpleText"]
                    videos_search = VideosSearch(search_query, limit=limit)
                    return videos_search.result()
                return {"result": []}
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, _get_related)
            
            videos = []
            for video in results["result"]:
                if video["id"] != video_id:  # 원본 비디오 제외
                    video_info = self._format_video_info(video)
                    if video_info:
                        videos.append(video_info)
            
            return videos[:limit]
            
        except Exception as e:
            self.logger.error(f"YouTube 관련 비디오 조회 실패: {e}")
            return []
    
    async def get_playlist_videos(self, playlist_url: str, limit: int = 50) -> List[Dict[str, Any]]:
        """플레이리스트 비디오 목록 가져오기"""
        if not YOUTUBE_DL_AVAILABLE:
            return []
        
        try:
            def _extract_playlist():
                with youtube_dl.YoutubeDL(self.ytdl_opts) as ydl:
                    return ydl.extract_info(playlist_url, download=False)
            
            loop = asyncio.get_event_loop()
            playlist_info = await loop.run_in_executor(None, _extract_playlist)
            
            videos = []
            entries = playlist_info.get("entries", [])
            
            for entry in entries[:limit]:
                if entry:
                    video_info = self._format_video_info_from_ytdl(entry)
                    # 적절한 길이의 비디오만 포함
                    if video_info and video_info["duration"] <= 600:  # 10분 이하
                        videos.append(video_info)
            
            return videos
            
        except Exception as e:
            self.logger.error(f"YouTube 플레이리스트 조회 실패: {e}")
            return []
    
    def is_youtube_url(self, url: str) -> bool:
        """YouTube URL 여부 확인"""
        youtube_patterns = [
            r"youtube\.com/watch",
            r"youtu\.be/",
            r"youtube\.com/embed/",
            r"youtube\.com/v/"
        ]
        
        return any(re.search(pattern, url) for pattern in youtube_patterns)
    
    def is_available(self) -> bool:
        """YouTube 통합 사용 가능 여부"""
        return YOUTUBE_DL_AVAILABLE and YOUTUBE_SEARCH_AVAILABLE
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        success_rate = 0
        if self.stats["successful_extractions"] + self.stats["failed_extractions"] > 0:
            success_rate = self.stats["successful_extractions"] / (
                self.stats["successful_extractions"] + self.stats["failed_extractions"]
            )
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "search_cache_size": len(self.search_cache),
            "video_cache_size": len(self.video_cache),
            "available": self.is_available()
        }
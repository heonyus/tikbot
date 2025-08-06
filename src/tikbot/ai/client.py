"""
Serena MCP 클라이언트
"""

import asyncio
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiohttp

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class SerenaClient:
    """Serena MCP 서버와 통신하는 클라이언트"""
    
    def __init__(self, 
                 server_url: str = "http://localhost:8000",
                 api_key: Optional[str] = None,
                 timeout: int = 30,
                 logger: Optional[logging.Logger] = None):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        
        # 연결 상태
        self.is_connected = False
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 요청 통계
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "last_request_time": None
        }
    
    async def initialize(self) -> bool:
        """클라이언트 초기화 및 연결 확인"""
        try:
            # HTTP 세션 생성
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
            
            # 연결 테스트
            await self._test_connection()
            
            self.is_connected = True
            self.logger.info(f"🤖 Serena MCP 클라이언트 연결 성공: {self.server_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Serena MCP 클라이언트 초기화 실패: {e}")
            self.is_connected = False
            return False
    
    async def _test_connection(self):
        """연결 테스트"""
        if not self.session:
            raise Exception("HTTP 세션이 초기화되지 않았습니다")
        
        try:
            # 기본 헬스체크 엔드포인트 시도
            async with self.session.get(f"{self.server_url}/health") as response:
                if response.status == 200:
                    return
        except:
            pass
        
        # OpenAPI 스키마 엔드포인트 시도
        try:
            async with self.session.get(f"{self.server_url}/openapi.json") as response:
                if response.status == 200:
                    return
        except:
            pass
        
        # 루트 엔드포인트 시도
        async with self.session.get(f"{self.server_url}/") as response:
            if response.status not in [200, 404]:  # 404도 서버가 응답한다는 의미
                response.raise_for_status()
    
    async def send_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Serena에게 메시지 전송"""
        if not self.is_connected or not self.session:
            raise Exception("Serena 클라이언트가 연결되지 않았습니다")
        
        start_time = datetime.now()
        self.stats["total_requests"] += 1
        
        try:
            # 요청 데이터 구성
            request_data = {
                "message": message,
                "context": context or {},
                "timestamp": start_time.isoformat()
            }
            
            # MCP 프로토콜에 따른 요청 (임시로 일반 API 형태로 구현)
            async with self.session.post(
                f"{self.server_url}/chat", 
                json=request_data
            ) as response:
                
                response_time = (datetime.now() - start_time).total_seconds()
                self._update_stats(response_time, True)
                
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "response": result.get("response", ""),
                        "metadata": result.get("metadata", {}),
                        "response_time": response_time
                    }
                else:
                    error_text = await response.text()
                    self.logger.error(f"Serena API 오류 ({response.status}): {error_text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "response_time": response_time
                    }
        
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(response_time, False)
            
            self.logger.error(f"Serena 요청 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": response_time
            }
    
    async def analyze_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """코드 분석 요청"""
        context = {
            "action": "analyze_code",
            "language": language,
            "project": "tikbot"
        }
        
        message = f"다음 {language} 코드를 분석해주세요:\n\n```{language}\n{code}\n```"
        return await self.send_message(message, context)
    
    async def get_suggestions(self, chat_message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """채팅 메시지에 대한 응답 제안"""
        context = {
            "action": "get_chat_suggestions",
            "user_info": user_context,
            "chat_context": {
                "platform": "tiktok_live",
                "stream_type": "interactive"
            }
        }
        
        message = f"TikTok Live 방송에서 시청자가 다음 메시지를 보냈습니다: '{chat_message}'\n적절한 응답을 제안해주세요."
        return await self.send_message(message, context)
    
    async def generate_auto_response(self, 
                                   trigger_keyword: str, 
                                   user_nickname: str,
                                   stream_context: Dict[str, Any]) -> Dict[str, Any]:
        """자동 응답 생성"""
        context = {
            "action": "generate_auto_response",
            "trigger": trigger_keyword,
            "stream_stats": stream_context
        }
        
        message = f"시청자 '{user_nickname}'가 '{trigger_keyword}' 키워드를 사용했습니다. 자연스러운 자동 응답을 생성해주세요."
        return await self.send_message(message, context)
    
    async def analyze_viewer_pattern(self, viewer_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """시청자 패턴 분석"""
        context = {
            "action": "analyze_viewer_pattern",
            "data_points": len(viewer_data)
        }
        
        message = f"다음 시청자 데이터를 분석하여 패턴과 인사이트를 제공해주세요:\n{json.dumps(viewer_data, indent=2, ensure_ascii=False)}"
        return await self.send_message(message, context)
    
    async def optimize_stream_settings(self, current_settings: Dict[str, Any], 
                                     performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """방송 설정 최적화 제안"""
        context = {
            "action": "optimize_stream_settings",
            "current_config": current_settings,
            "performance": performance_data
        }
        
        message = "현재 방송 설정과 성능 데이터를 바탕으로 최적화 방안을 제안해주세요."
        return await self.send_message(message, context)
    
    def _update_stats(self, response_time: float, success: bool):
        """통계 업데이트"""
        if success:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1
        
        # 평균 응답 시간 계산
        total_requests = self.stats["total_requests"]
        current_avg = self.stats["average_response_time"]
        new_avg = ((current_avg * (total_requests - 1)) + response_time) / total_requests
        self.stats["average_response_time"] = new_avg
        
        self.stats["last_request_time"] = datetime.now().isoformat()
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록 조회"""
        if not self.is_connected or not self.session:
            return []
        
        try:
            async with self.session.get(f"{self.server_url}/tools") as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("tools", [])
        except Exception as e:
            self.logger.error(f"도구 목록 조회 실패: {e}")
        
        return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """특정 도구 호출"""
        if not self.is_connected or not self.session:
            raise Exception("Serena 클라이언트가 연결되지 않았습니다")
        
        try:
            request_data = {
                "tool": tool_name,
                "arguments": arguments
            }
            
            async with self.session.post(
                f"{self.server_url}/tools/{tool_name}",
                json=request_data
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}"
                    }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """클라이언트 통계 반환"""
        success_rate = 0
        if self.stats["total_requests"] > 0:
            success_rate = self.stats["successful_requests"] / self.stats["total_requests"]
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "is_connected": self.is_connected,
            "server_url": self.server_url
        }
    
    async def cleanup(self):
        """리소스 정리"""
        if self.session:
            await self.session.close()
            self.session = None
        
        self.is_connected = False
        self.logger.info("Serena 클라이언트 정리 완료")
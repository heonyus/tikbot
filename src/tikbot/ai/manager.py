"""
AI Manager - Serena 통합 및 지능형 응답 관리
"""

import asyncio
import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

from .client import SerenaClient
from .conversation import ConversationContext, ConversationMessage, MessageType
from ..core.events import EventHandler, EventType, Event


class AIManager:
    """AI 통합 매니저"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.enabled = config.get('enabled', True)
        
        # Serena 클라이언트
        self.serena_client: Optional[SerenaClient] = None
        
        # 대화 컨텍스트
        self.conversation = ConversationContext(
            max_history=config.get('max_history', 200),
            context_window=config.get('context_window', 15),
            logger=self.logger
        )
        
        # AI 응답 설정
        self.ai_response_enabled = config.get('ai_response_enabled', True)
        self.ai_response_rate = config.get('ai_response_rate', 0.3)  # 30% 확률로 AI 응답
        self.ai_response_cooldown = config.get('ai_response_cooldown', 10)  # 10초 쿨다운
        self.last_ai_response_time = None
        
        # 스마트 기능 설정
        self.smart_auto_response = config.get('smart_auto_response', True)
        self.pattern_learning = config.get('pattern_learning', True)
        self.context_awareness = config.get('context_awareness', True)
        
        # 통계
        self.stats = {
            "initialization_time": None,
            "total_ai_responses": 0,
            "successful_ai_responses": 0,
            "failed_ai_responses": 0,
            "context_updates": 0,
            "learning_insights": 0
        }
    
    async def initialize(self) -> bool:
        """AI 시스템 초기화"""
        if not self.enabled:
            self.logger.info("AI 시스템이 비활성화되어 있습니다.")
            return True
        
        try:
            import time
            start_time = time.time()
            
            # Serena 클라이언트 초기화
            serena_config = self.config.get('serena', {})
            if serena_config.get('enabled', True):
                self.serena_client = SerenaClient(
                    server_url=serena_config.get('server_url', 'http://localhost:8000'),
                    api_key=serena_config.get('api_key'),
                    timeout=serena_config.get('timeout', 30),
                    logger=self.logger
                )
                
                if not await self.serena_client.initialize():
                    self.logger.warning("Serena 클라이언트 초기화 실패 - AI 기능이 제한됩니다")
                    self.serena_client = None
            
            # 초기화 시간 기록
            self.stats["initialization_time"] = time.time() - start_time
            
            if self.serena_client:
                self.logger.info("🤖 AI 시스템 초기화 완료 - Serena 통합 활성화")
            else:
                self.logger.info("🤖 AI 시스템 초기화 완료 - 로컬 AI 기능만 활성화")
            
            return True
            
        except Exception as e:
            self.logger.error(f"AI 시스템 초기화 실패: {e}")
            return False
    
    def register_event_handlers(self, event_handler: EventHandler):
        """이벤트 핸들러에 AI 이벤트 등록"""
        if not self.enabled:
            return
        
        @event_handler.on(EventType.COMMENT)
        async def on_comment_for_ai(event_data):
            await self.handle_comment(event_data)
        
        @event_handler.on(EventType.GIFT)
        async def on_gift_for_ai(event_data):
            await self.handle_gift(event_data)
        
        @event_handler.on(EventType.FOLLOW)
        async def on_follow_for_ai(event_data):
            await self.handle_follow(event_data)
        
        @event_handler.on(EventType.COMMAND)
        async def on_ai_command(event_data):
            command = event_data.get("command", "").lower()
            username = event_data.get("username", "")
            nickname = event_data.get("nickname", username)
            args = event_data.get("args", [])
            
            # AI 질문 명령어
            if command == "!ai":
                if args:
                    question = " ".join(args)
                    await self._handle_ai_question(question, username, nickname)
                else:
                    self.logger.info(f"🤖 AI 사용법: !ai 질문을 입력하세요")
            
            # 인사이트 명령어
            elif command == "!insights":
                await self._handle_insights_request(username, nickname)
        
        self.logger.info("AI 이벤트 핸들러 등록 완료")
    
    async def handle_comment(self, event_data: Dict[str, Any]):
        """댓글 이벤트 처리"""
        username = event_data.get("username", "")
        nickname = event_data.get("nickname", username)
        comment = event_data.get("comment", "")
        
        # 대화 컨텍스트에 메시지 추가
        message = ConversationMessage(
            id=f"comment_{datetime.now().timestamp()}",
            type=MessageType.USER_COMMENT,
            content=comment,
            username=username,
            nickname=nickname,
            timestamp=datetime.now(),
            metadata=event_data
        )
        
        self.conversation.add_message(message)
        self.stats["context_updates"] += 1
        
        # AI 응답 결정
        if await self._should_generate_ai_response(comment, username):
            await self._generate_ai_response(comment, username, nickname)
    
    async def handle_gift(self, event_data: Dict[str, Any]):
        """선물 이벤트 처리"""
        username = event_data.get("username", "")
        nickname = event_data.get("nickname", username)
        gift_name = event_data.get("gift_name", "")
        gift_count = event_data.get("gift_count", 1)
        
        # 대화 컨텍스트에 선물 이벤트 추가
        message = ConversationMessage(
            id=f"gift_{datetime.now().timestamp()}",
            type=MessageType.SYSTEM_MESSAGE,
            content=f"{nickname}님이 {gift_name} {gift_count}개를 선물했습니다!",
            username=username,
            nickname=nickname,
            timestamp=datetime.now(),
            metadata={"gift_count": gift_count, **event_data}
        )
        
        self.conversation.add_message(message)
        
        # 선물에 대한 AI 감사 응답
        if self.ai_response_enabled and self.serena_client:
            await self._generate_gift_thanks_response(nickname, gift_name, gift_count)
    
    async def handle_follow(self, event_data: Dict[str, Any]):
        """팔로우 이벤트 처리"""
        username = event_data.get("username", "")
        nickname = event_data.get("nickname", username)
        
        # 대화 컨텍스트에 팔로우 이벤트 추가
        message = ConversationMessage(
            id=f"follow_{datetime.now().timestamp()}",
            type=MessageType.SYSTEM_MESSAGE,
            content=f"{nickname}님이 팔로우했습니다!",
            username=username,
            nickname=nickname,
            timestamp=datetime.now(),
            metadata={"is_follower": True, **event_data}
        )
        
        self.conversation.add_message(message)
        
        # 팔로우에 대한 AI 환영 응답
        if self.ai_response_enabled and self.serena_client:
            await self._generate_welcome_response(nickname)
    
    async def _should_generate_ai_response(self, comment: str, username: str) -> bool:
        """AI 응답 생성 여부 결정"""
        # 기본 조건 확인
        if not self.ai_response_enabled or not self.serena_client:
            return False
        
        # 쿨다운 확인
        if self.last_ai_response_time:
            time_since_last = (datetime.now() - self.last_ai_response_time).total_seconds()
            if time_since_last < self.ai_response_cooldown:
                return False
        
        # 확률 기반 응답
        if random.random() > self.ai_response_rate:
            return False
        
        # 컨텍스트 기반 조건들
        if self.context_awareness:
            # 질문이 포함된 경우 높은 우선순위
            if any(q in comment.lower() for q in ['?', '물어', '궁금', '어떻게', '뭐', '왜']):
                return True
            
            # 봇을 직접 언급한 경우
            if any(mention in comment.lower() for mention in ['봇', 'bot', 'ai', '로봇']):
                return True
            
            # 인기 토픽에 대한 언급
            stream_insights = self.conversation.get_stream_insights()
            active_topics = stream_insights["stream_context"]["active_topics"]
            if any(topic in comment.lower() for topic in active_topics):
                return True
        
        # 기본 확률 적용
        return random.random() < 0.2  # 20% 기본 확률
    
    async def _generate_ai_response(self, comment: str, username: str, nickname: str):
        """AI 응답 생성"""
        try:
            # 사용자 컨텍스트 수집
            user_context = self.conversation.get_user_context(username) or {}
            stream_insights = self.conversation.get_stream_insights()
            
            # Serena에 응답 요청
            result = await self.serena_client.get_suggestions(comment, {
                "user": user_context,
                "stream": stream_insights,
                "recent_context": self.conversation.get_recent_context()
            })
            
            if result["success"]:
                ai_response = result["response"]
                
                # AI 응답을 대화 컨텍스트에 추가
                response_message = ConversationMessage(
                    id=f"ai_response_{datetime.now().timestamp()}",
                    type=MessageType.AI_SUGGESTION,
                    content=ai_response,
                    username="tikbot_ai",
                    nickname="TikBot AI",
                    timestamp=datetime.now(),
                    metadata={"original_comment": comment, "target_user": nickname}
                )
                
                self.conversation.add_message(response_message)
                
                # 통계 업데이트
                self.stats["total_ai_responses"] += 1
                self.stats["successful_ai_responses"] += 1
                self.last_ai_response_time = datetime.now()
                
                self.logger.info(f"🤖 AI 응답 생성: {nickname}에게 '{ai_response}'")
                
                # 실제 채팅으로 응답 전송은 봇의 다른 부분에서 처리
                
            else:
                self.stats["failed_ai_responses"] += 1
                self.logger.warning(f"AI 응답 생성 실패: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            self.stats["failed_ai_responses"] += 1
            self.logger.error(f"AI 응답 생성 중 오류: {e}")
    
    async def _generate_gift_thanks_response(self, nickname: str, gift_name: str, gift_count: int):
        """선물 감사 응답 생성"""
        if not self.serena_client:
            return
        
        try:
            context = {
                "action": "gift_thanks",
                "gift_info": {
                    "name": gift_name,
                    "count": gift_count,
                    "giver": nickname
                }
            }
            
            message = f"{nickname}님이 {gift_name} {gift_count}개를 선물해주셨습니다. 적절한 감사 인사를 해주세요."
            
            result = await self.serena_client.send_message(message, context)
            
            if result["success"]:
                self.logger.info(f"🎁 선물 감사 AI 응답: {result['response']}")
                # 응답 처리 로직 추가
            
        except Exception as e:
            self.logger.error(f"선물 감사 응답 생성 실패: {e}")
    
    async def _generate_welcome_response(self, nickname: str):
        """환영 응답 생성"""
        if not self.serena_client:
            return
        
        try:
            stream_insights = self.conversation.get_stream_insights()
            
            context = {
                "action": "welcome_new_follower",
                "stream_context": stream_insights
            }
            
            message = f"{nickname}님이 새로 팔로우하셨습니다. 따뜻한 환영 인사를 해주세요."
            
            result = await self.serena_client.send_message(message, context)
            
            if result["success"]:
                self.logger.info(f"👋 팔로우 환영 AI 응답: {result['response']}")
                # 응답 처리 로직 추가
            
        except Exception as e:
            self.logger.error(f"환영 응답 생성 실패: {e}")
    
    async def enhance_auto_response(self, keyword: str, user_context: Dict[str, Any]) -> str:
        """자동 응답 향상"""
        if not self.smart_auto_response or not self.serena_client:
            return ""  # 기본 자동 응답 사용
        
        try:
            result = await self.serena_client.generate_auto_response(
                keyword, 
                user_context.get("nickname", ""),
                self.conversation.get_stream_insights()
            )
            
            if result["success"]:
                return result["response"]
            
        except Exception as e:
            self.logger.error(f"자동 응답 향상 실패: {e}")
        
        return ""  # 실패 시 기본 응답 사용
    
    async def analyze_stream_performance(self) -> Dict[str, Any]:
        """방송 성능 분석"""
        if not self.serena_client:
            return {}
        
        try:
            insights = self.conversation.get_stream_insights()
            learning_data = self.conversation.export_learning_data()
            
            result = await self.serena_client.analyze_viewer_pattern(
                learning_data["user_profiles"]
            )
            
            if result["success"]:
                self.stats["learning_insights"] += 1
                return {
                    "ai_analysis": result["response"],
                    "local_insights": insights,
                    "learning_data": learning_data
                }
            
        except Exception as e:
            self.logger.error(f"방송 성능 분석 실패: {e}")
        
        return {}
    
    async def get_optimization_suggestions(self) -> List[str]:
        """최적화 제안 가져오기"""
        if not self.serena_client:
            return []
        
        try:
            current_settings = {
                "ai_response_rate": self.ai_response_rate,
                "ai_response_cooldown": self.ai_response_cooldown,
                "context_window": self.conversation.context_window
            }
            
            performance_data = {
                "stats": self.stats,
                "stream_insights": self.conversation.get_stream_insights()
            }
            
            result = await self.serena_client.optimize_stream_settings(
                current_settings, performance_data
            )
            
            if result["success"]:
                return result["response"].split('\n') if isinstance(result["response"], str) else []
            
        except Exception as e:
            self.logger.error(f"최적화 제안 가져오기 실패: {e}")
        
        return []
    
    async def _handle_ai_question(self, question: str, username: str, nickname: str):
        """AI 질문 처리"""
        if not self.serena_client:
            self.logger.info(f"🤖 {nickname}: AI 시스템이 비활성화되어 있습니다")
            return
        
        try:
            # 사용자 컨텍스트 수집
            user_context = self.conversation.get_user_context(username) or {}
            stream_insights = self.conversation.get_stream_insights()
            
            # AI에게 질문 전송
            result = await self.serena_client.send_message(question, {
                "action": "direct_question",
                "user": user_context,
                "stream": stream_insights,
                "context": self.conversation.get_recent_context()
            })
            
            if result["success"]:
                response = result["response"]
                self.logger.info(f"🤖 AI 응답 to {nickname}: {response}")
                
                # 응답을 대화 컨텍스트에 추가
                response_message = ConversationMessage(
                    id=f"ai_question_{datetime.now().timestamp()}",
                    type=MessageType.AI_SUGGESTION,
                    content=response,
                    username="tikbot_ai",
                    nickname="TikBot AI",
                    timestamp=datetime.now(),
                    metadata={
                        "original_question": question, 
                        "questioner": nickname,
                        "response_type": "direct_question"
                    }
                )
                
                self.conversation.add_message(response_message)
                self.stats["successful_ai_responses"] += 1
                
            else:
                self.logger.warning(f"🤖 AI 질문 처리 실패: {result.get('error', 'Unknown error')}")
                self.stats["failed_ai_responses"] += 1
        
        except Exception as e:
            self.logger.error(f"AI 질문 처리 중 오류: {e}")
            self.stats["failed_ai_responses"] += 1
    
    async def _handle_insights_request(self, username: str, nickname: str):
        """인사이트 요청 처리"""
        try:
            insights = self.conversation.get_stream_insights()
            user_analytics = self.get_user_analytics()
            
            # 간단한 인사이트 요약
            summary = [
                f"📊 현재 시청자: {insights['stream_context']['viewer_count']}명",
                f"💬 총 메시지: {insights['stream_context']['total_messages']}개",
                f"🎁 총 선물: {insights['stream_context']['total_gifts']}개",
                f"👥 총 사용자: {user_analytics['total_users']}명",
                f"🎯 분위기: {insights['stream_context']['mood']}",
                f"⚡ 에너지: {insights['stream_context']['energy_level']}"
            ]
            
            # 인기 토픽 추가
            if insights['stream_context']['active_topics']:
                topics = ", ".join(insights['stream_context']['active_topics'][:3])
                summary.append(f"🔥 인기 토픽: {topics}")
            
            insight_text = "\n".join(summary)
            self.logger.info(f"📊 인사이트 to {nickname}:\n{insight_text}")
            
            # Serena가 있다면 더 상세한 분석 요청
            if self.serena_client:
                detailed_analysis = await self.analyze_stream_performance()
                if detailed_analysis and "ai_analysis" in detailed_analysis:
                    self.logger.info(f"🤖 AI 상세 분석: {detailed_analysis['ai_analysis']}")
        
        except Exception as e:
            self.logger.error(f"인사이트 요청 처리 중 오류: {e}")
    
    def get_conversation_insights(self) -> Dict[str, Any]:
        """대화 인사이트 반환"""
        return self.conversation.get_stream_insights()
    
    def get_user_analytics(self) -> Dict[str, Any]:
        """사용자 분석 데이터"""
        profiles = self.conversation.user_profiles
        
        # 참여도별 사용자 분류
        engagement_levels = {"high": 0, "medium": 0, "low": 0}
        for profile in profiles.values():
            level = self.conversation._calculate_engagement_level(profile)
            engagement_levels[level] += 1
        
        # 활성 시간대 분석
        peak_hours = {}
        for entry in self.conversation.learning_data["peak_activity_times"]:
            peak_hours[entry["hour"]] = entry["message_count"]
        
        return {
            "total_users": len(profiles),
            "engagement_distribution": engagement_levels,
            "peak_activity_hours": peak_hours,
            "top_users": sorted(
                [(p.username, p.nickname, p.message_count) for p in profiles.values()],
                key=lambda x: x[2], reverse=True
            )[:10]
        }
    
    def update_settings(self, settings: Dict[str, Any]):
        """설정 업데이트"""
        if "ai_response_enabled" in settings:
            self.ai_response_enabled = settings["ai_response_enabled"]
        
        if "ai_response_rate" in settings:
            self.ai_response_rate = max(0.0, min(1.0, settings["ai_response_rate"]))
        
        if "ai_response_cooldown" in settings:
            self.ai_response_cooldown = max(1, settings["ai_response_cooldown"])
        
        if "context_window" in settings:
            self.conversation.context_window = max(5, settings["context_window"])
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        stats = self.stats.copy()
        
        # 성공률 계산
        ai_success_rate = 0
        if self.stats["total_ai_responses"] > 0:
            ai_success_rate = self.stats["successful_ai_responses"] / self.stats["total_ai_responses"]
        
        # Serena 클라이언트 통계 추가
        serena_stats = {}
        if self.serena_client:
            serena_stats = self.serena_client.get_stats()
        
        stats.update({
            "enabled": self.enabled,
            "ai_success_rate": ai_success_rate,
            "serena_available": self.serena_client is not None,
            "serena_stats": serena_stats,
            "conversation_stats": {
                "total_messages": len(self.conversation.messages),
                "total_users": len(self.conversation.user_profiles),
                "stream_context": self.conversation.stream_context
            }
        })
        
        return stats
    
    async def cleanup(self):
        """리소스 정리"""
        if self.serena_client:
            await self.serena_client.cleanup()
        
        # 학습 데이터 저장 (필요시)
        self.conversation.clear_old_data()
        
        self.logger.info("AI 매니저 정리 완료")
"""
데이터 시각화 - 차트 및 그래프 생성
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import base64
from io import BytesIO

# 시각화 라이브러리 (optional)
try:
    import matplotlib
    matplotlib.use('Agg')  # GUI 없는 환경에서 사용
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.utils import PlotlyJSONEncoder
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class DataVisualizer:
    """데이터 시각화 생성기"""
    
    def __init__(self, theme: str = "dark", logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.theme = theme
        
        # 테마 설정
        self.colors = {
            "dark": {
                "primary": "#667eea",
                "secondary": "#764ba2", 
                "success": "#10b981",
                "warning": "#f59e0b",
                "danger": "#ef4444",
                "background": "#1f2937",
                "text": "#f9fafb"
            },
            "light": {
                "primary": "#3b82f6",
                "secondary": "#8b5cf6",
                "success": "#059669",
                "warning": "#d97706",
                "danger": "#dc2626",
                "background": "#ffffff",
                "text": "#111827"
            }
        }
        
        self.current_colors = self.colors.get(theme, self.colors["dark"])
    
    async def create_engagement_chart(self, data: Dict[str, Any], 
                                    chart_type: str = "plotly") -> Dict[str, Any]:
        """참여도 차트 생성"""
        try:
            if chart_type == "plotly" and PLOTLY_AVAILABLE:
                return await self._create_plotly_engagement_chart(data)
            elif chart_type == "matplotlib" and MATPLOTLIB_AVAILABLE:
                return await self._create_matplotlib_engagement_chart(data)
            else:
                return await self._create_text_chart(data, "참여도")
        
        except Exception as e:
            self.logger.error(f"참여도 차트 생성 실패: {e}")
            return {"error": str(e)}
    
    async def create_trend_chart(self, data: Dict[str, Any],
                               chart_type: str = "plotly") -> Dict[str, Any]:
        """트렌드 차트 생성"""
        try:
            if chart_type == "plotly" and PLOTLY_AVAILABLE:
                return await self._create_plotly_trend_chart(data)
            elif chart_type == "matplotlib" and MATPLOTLIB_AVAILABLE:
                return await self._create_matplotlib_trend_chart(data)
            else:
                return await self._create_text_chart(data, "트렌드")
        
        except Exception as e:
            self.logger.error(f"트렌드 차트 생성 실패: {e}")
            return {"error": str(e)}
    
    async def create_user_distribution_chart(self, data: Dict[str, Any],
                                           chart_type: str = "plotly") -> Dict[str, Any]:
        """사용자 분포 차트 생성"""
        try:
            if chart_type == "plotly" and PLOTLY_AVAILABLE:
                return await self._create_plotly_user_chart(data)
            elif chart_type == "matplotlib" and MATPLOTLIB_AVAILABLE:
                return await self._create_matplotlib_user_chart(data)
            else:
                return await self._create_text_chart(data, "사용자 분포")
        
        except Exception as e:
            self.logger.error(f"사용자 분포 차트 생성 실패: {e}")
            return {"error": str(e)}
    
    async def create_dashboard_summary(self, 
                                     engagement_data: Dict[str, Any],
                                     trend_data: Dict[str, Any],
                                     behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """대시보드 요약 생성"""
        try:
            # 핵심 메트릭 추출
            metrics = {
                "engagement_score": engagement_data.get("engagement_score", 0),
                "total_events": engagement_data.get("total_events", 0),
                "unique_users": engagement_data.get("unique_users", 0),
                "growth_score": trend_data.get("growth_score", 0),
                "high_engagement_users": behavior_data.get("engagement_distribution", {}).get("high", 0)
            }
            
            # 상태 표시기
            status_indicators = []
            
            # 참여도 상태
            engagement_score = metrics["engagement_score"]
            if engagement_score >= 80:
                status_indicators.append({
                    "type": "success",
                    "title": "참여도 우수",
                    "value": f"{engagement_score:.1f}/100",
                    "icon": "🔥"
                })
            elif engagement_score >= 50:
                status_indicators.append({
                    "type": "warning", 
                    "title": "참여도 보통",
                    "value": f"{engagement_score:.1f}/100",
                    "icon": "⚡"
                })
            else:
                status_indicators.append({
                    "type": "danger",
                    "title": "참여도 낮음",
                    "value": f"{engagement_score:.1f}/100",
                    "icon": "📉"
                })
            
            # 성장 상태
            growth_score = metrics["growth_score"]
            if growth_score >= 50:
                status_indicators.append({
                    "type": "success",
                    "title": "성장세",
                    "value": f"+{growth_score:.1f}%",
                    "icon": "📈"
                })
            elif growth_score >= 0:
                status_indicators.append({
                    "type": "warning",
                    "title": "안정세",
                    "value": f"{growth_score:.1f}%",
                    "icon": "➡️"
                })
            else:
                status_indicators.append({
                    "type": "danger",
                    "title": "하락세",
                    "value": f"{growth_score:.1f}%",
                    "icon": "📉"
                })
            
            # 활성 사용자
            unique_users = metrics["unique_users"]
            if unique_users >= 50:
                user_status = "success"
                user_icon = "👥"
            elif unique_users >= 20:
                user_status = "warning"
                user_icon = "👤"
            else:
                user_status = "danger"
                user_icon = "👁️"
            
            status_indicators.append({
                "type": user_status,
                "title": "활성 사용자",
                "value": f"{unique_users}명",
                "icon": user_icon
            })
            
            # 추천 액션
            recommendations = []
            
            if engagement_score < 50:
                recommendations.append({
                    "priority": "high",
                    "action": "참여도 향상",
                    "description": "인터랙티브 콘텐츠나 Q&A 세션을 시도해보세요",
                    "icon": "🎯"
                })
            
            if unique_users < 20:
                recommendations.append({
                    "priority": "medium",
                    "action": "시청자 확보",
                    "description": "소셜미디어 홍보나 협업을 고려해보세요",
                    "icon": "📢"
                })
            
            if growth_score < 0:
                recommendations.append({
                    "priority": "high", 
                    "action": "성장 전략 재검토",
                    "description": "콘텐츠 전략이나 방송 시간을 조정해보세요",
                    "icon": "🔄"
                })
            
            return {
                "metrics": metrics,
                "status_indicators": status_indicators,
                "recommendations": recommendations,
                "last_updated": datetime.now().isoformat(),
                "theme": self.theme
            }
            
        except Exception as e:
            self.logger.error(f"대시보드 요약 생성 실패: {e}")
            return {"error": str(e)}
    
    async def _create_plotly_engagement_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Plotly 참여도 차트"""
        if not PLOTLY_AVAILABLE:
            return {"error": "Plotly not available"}
        
        # 이벤트 타입별 차트
        event_breakdown = data.get("event_breakdown", {})
        
        if not event_breakdown:
            return {"error": "No event data available"}
        
        # 파이 차트
        fig = go.Figure(data=[go.Pie(
            labels=list(event_breakdown.keys()),
            values=list(event_breakdown.values()),
            marker_colors=[
                self.current_colors["primary"],
                self.current_colors["secondary"],
                self.current_colors["success"],
                self.current_colors["warning"],
                self.current_colors["danger"]
            ][:len(event_breakdown)]
        )])
        
        fig.update_layout(
            title="이벤트 타입별 분포",
            paper_bgcolor=self.current_colors["background"],
            plot_bgcolor=self.current_colors["background"],
            font_color=self.current_colors["text"],
            showlegend=True
        )
        
        return {
            "type": "plotly",
            "chart": json.loads(fig.to_json()),
            "title": "참여도 분석"
        }
    
    async def _create_plotly_trend_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Plotly 트렌드 차트"""
        if not PLOTLY_AVAILABLE:
            return {"error": "Plotly not available"}
        
        trends = data.get("trends", {})
        dates = data.get("dates", [])
        
        if not trends or not dates:
            return {"error": "No trend data available"}
        
        fig = go.Figure()
        
        # 각 메트릭별 라인 추가
        colors = [
            self.current_colors["primary"],
            self.current_colors["secondary"], 
            self.current_colors["success"],
            self.current_colors["warning"]
        ]
        
        color_idx = 0
        for metric, trend_data in trends.items():
            if "values" in trend_data:
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=trend_data["values"],
                    mode='lines+markers',
                    name=metric,
                    line=dict(color=colors[color_idx % len(colors)])
                ))
                color_idx += 1
        
        fig.update_layout(
            title="일별 트렌드",
            xaxis_title="날짜",
            yaxis_title="값",
            paper_bgcolor=self.current_colors["background"],
            plot_bgcolor=self.current_colors["background"],
            font_color=self.current_colors["text"],
            showlegend=True
        )
        
        return {
            "type": "plotly",
            "chart": json.loads(fig.to_json()),
            "title": "성장 트렌드"
        }
    
    async def _create_plotly_user_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Plotly 사용자 분포 차트"""
        if not PLOTLY_AVAILABLE:
            return {"error": "Plotly not available"}
        
        engagement_dist = data.get("engagement_distribution", {})
        
        if not engagement_dist:
            return {"error": "No user distribution data available"}
        
        # 막대 차트
        fig = go.Figure(data=[
            go.Bar(
                x=list(engagement_dist.keys()),
                y=list(engagement_dist.values()),
                marker_color=[
                    self.current_colors["success"],
                    self.current_colors["warning"],
                    self.current_colors["danger"]
                ]
            )
        ])
        
        fig.update_layout(
            title="사용자 참여도 분포",
            xaxis_title="참여도 레벨",
            yaxis_title="사용자 수",
            paper_bgcolor=self.current_colors["background"],
            plot_bgcolor=self.current_colors["background"],
            font_color=self.current_colors["text"]
        )
        
        return {
            "type": "plotly",
            "chart": json.loads(fig.to_json()),
            "title": "사용자 분포"
        }
    
    async def _create_matplotlib_engagement_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Matplotlib 참여도 차트"""
        if not MATPLOTLIB_AVAILABLE:
            return {"error": "Matplotlib not available"}
        
        # 플롯 설정
        plt.style.use('dark_background' if self.theme == "dark" else 'default')
        
        event_breakdown = data.get("event_breakdown", {})
        
        if not event_breakdown:
            return {"error": "No event data available"}
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 파이 차트
        wedges, texts, autotexts = ax.pie(
            list(event_breakdown.values()),
            labels=list(event_breakdown.keys()),
            autopct='%1.1f%%',
            startangle=90
        )
        
        ax.set_title("이벤트 타입별 분포", fontsize=16)
        
        # 이미지를 base64로 인코딩
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return {
            "type": "matplotlib",
            "image": f"data:image/png;base64,{image_base64}",
            "title": "참여도 분석"
        }
    
    async def _create_matplotlib_trend_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Matplotlib 트렌드 차트"""
        if not MATPLOTLIB_AVAILABLE:
            return {"error": "Matplotlib not available"}
        
        plt.style.use('dark_background' if self.theme == "dark" else 'default')
        
        trends = data.get("trends", {})
        dates = data.get("dates", [])
        
        if not trends or not dates:
            return {"error": "No trend data available"}
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 각 메트릭별 라인 플롯
        for metric, trend_data in trends.items():
            if "values" in trend_data:
                ax.plot(dates, trend_data["values"], marker='o', label=metric, linewidth=2)
        
        ax.set_title("일별 트렌드", fontsize=16)
        ax.set_xlabel("날짜")
        ax.set_ylabel("값")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 날짜 포맷팅
        if len(dates) > 7:
            ax.tick_params(axis='x', rotation=45)
        
        # 이미지를 base64로 인코딩
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return {
            "type": "matplotlib",
            "image": f"data:image/png;base64,{image_base64}",
            "title": "성장 트렌드"
        }
    
    async def _create_matplotlib_user_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Matplotlib 사용자 분포 차트"""
        if not MATPLOTLIB_AVAILABLE:
            return {"error": "Matplotlib not available"}
        
        plt.style.use('dark_background' if self.theme == "dark" else 'default')
        
        engagement_dist = data.get("engagement_distribution", {})
        
        if not engagement_dist:
            return {"error": "No user distribution data available"}
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 막대 차트
        bars = ax.bar(
            list(engagement_dist.keys()),
            list(engagement_dist.values()),
            color=[self.current_colors["success"], self.current_colors["warning"], self.current_colors["danger"]]
        )
        
        ax.set_title("사용자 참여도 분포", fontsize=16)
        ax.set_xlabel("참여도 레벨")
        ax.set_ylabel("사용자 수")
        
        # 값 표시
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom')
        
        # 이미지를 base64로 인코딩
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return {
            "type": "matplotlib",
            "image": f"data:image/png;base64,{image_base64}",
            "title": "사용자 분포"
        }
    
    async def _create_text_chart(self, data: Dict[str, Any], chart_title: str) -> Dict[str, Any]:
        """텍스트 기반 차트 (fallback)"""
        
        # 간단한 ASCII 차트 생성
        chart_content = []
        chart_content.append(f"=== {chart_title} ===")
        
        if "engagement_score" in data:
            score = data["engagement_score"]
            bar_length = int(score / 5)  # 0-100을 0-20 바로 변환
            bar = "█" * bar_length + "░" * (20 - bar_length)
            chart_content.append(f"참여도: {bar} {score:.1f}/100")
        
        if "event_breakdown" in data:
            chart_content.append("\n이벤트 분포:")
            breakdown = data["event_breakdown"]
            total = sum(breakdown.values())
            for event_type, count in breakdown.items():
                percentage = (count / total * 100) if total > 0 else 0
                bar_length = int(percentage / 5)
                bar = "█" * bar_length + "░" * (20 - bar_length)
                chart_content.append(f"{event_type:10s}: {bar} {percentage:.1f}%")
        
        if "unique_users" in data:
            chart_content.append(f"\n활성 사용자: {data['unique_users']}명")
        
        if "total_events" in data:
            chart_content.append(f"총 이벤트: {data['total_events']}개")
        
        return {
            "type": "text",
            "content": "\n".join(chart_content),
            "title": chart_title
        }
    
    def get_available_formats(self) -> List[str]:
        """사용 가능한 차트 형식 반환"""
        formats = ["text"]
        
        if PLOTLY_AVAILABLE:
            formats.append("plotly")
        
        if MATPLOTLIB_AVAILABLE:
            formats.append("matplotlib")
        
        return formats
    
    def set_theme(self, theme: str):
        """테마 변경"""
        if theme in self.colors:
            self.theme = theme
            self.current_colors = self.colors[theme]
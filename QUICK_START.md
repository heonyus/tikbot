# 🚀 TikBot 빠른 시작 가이드

## 📋 시작하기 전에

### ✅ 필수 요구사항
- **Python 3.11+** 설치됨
- **uv** 패키지 매니저 설치됨
- **TikTok 계정** (방송할 계정)

### 📁 프로젝트 구조 확인
```
tikbot/
├── src/tikbot/          # 봇 소스코드
├── templates/           # 오버레이 템플릿
├── static/             # 정적 파일
├── data/               # 데이터 저장
├── logs/               # 로그 파일
├── config.yaml         # 설정 파일
└── env.example         # 환경변수 예제
```

## 🔧 1단계: 환경 설정

### 1. 환경 변수 설정
```bash
# env.example을 .env로 복사
copy env.example .env

# .env 파일 편집 (실제 TikTok 사용자명으로 변경)
TIKTOK_USERNAME=your_actual_tiktok_username
```

### 2. 의존성 설치 확인
```bash
uv sync
```

## 🚀 2단계: 봇 실행

### 기본 실행
```bash
uv run python -m src.tikbot.main
```

### 실행 성공 확인
```
✅ TikBot이 @your_username에 연결되었습니다!
🌐 API 서버 시작: http://localhost:8000
🎨 오버레이 WebSocket 서버 시작: ws://localhost:8080
📊 분석 시스템 초기화 완료
```

## 🌐 3단계: 웹 대시보드 접속

### 메인 대시보드
브라우저에서 접속: **http://localhost:8000**

### API 엔드포인트
- `GET /status` - 봇 상태 확인
- `GET /stats` - 실시간 통계
- `GET /analytics/dashboard` - 분석 대시보드
- `GET /music/queue` - 음악 큐
- `GET /ai/insights` - AI 인사이트

## 🎨 4단계: OBS 오버레이 설정

### OBS에서 브라우저 소스 추가

1. **소스 추가** → **브라우저**
2. **URL 입력**:

#### 🎯 추천 오버레이들
```
통합 대시보드:     http://localhost:8000/overlay/dashboard
Analytics 대시보드: http://localhost:8000/overlay/analytics
채팅 오버레이:     http://localhost:8000/overlay/chat
음악 플레이어:     http://localhost:8000/overlay/music
실시간 통계:      http://localhost:8000/overlay/stats
```

3. **크기 설정**: 
   - 너비: 1920px
   - 높이: 1080px
   - CSS 사용자 정의 가능

## 🎮 5단계: 채팅 명령어 사용

### 기본 명령어
```
!help        - 도움말
!stats       - 방송 통계
!music 아티스트 - 곡명  - 음악 요청
!ai 질문내용   - AI에게 질문
!analytics   - 분석 대시보드
!commands    - 전체 명령어
```

### 관리자 명령어
```
!skip        - 현재 곡 스킵
!insights    - 상세 인사이트
!trends      - 성장 트렌드
```

## ⚙️ 6단계: 고급 설정

### config.yaml 편집
```yaml
features:
  tts_enabled: true          # 음성 읽기 활성화
  music_enabled: true        # 음악 기능 활성화
  ai_enabled: true          # AI 기능 활성화
  analytics_enabled: true   # 분석 기능 활성화
```

### Spotify 연동 (선택사항)
1. [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) 접속
2. 앱 생성 후 Client ID/Secret 획득
3. config.yaml 편집:
```yaml
music:
  spotify:
    client_id: "your_client_id"
    client_secret: "your_client_secret"
```

### Serena AI 연동 (선택사항)
```bash
# 별도 터미널에서 Serena 서버 실행
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --transport sse --port 8000
```

## 🔧 문제 해결

### 일반적인 문제들

#### 1. 연결 실패
```
❌ TikTok 연결 실패
```
**해결**: TikTok 사용자명 확인, 방송 중인지 확인

#### 2. 포트 충돌
```
❌ Port 8000 already in use
```
**해결**: config.yaml에서 포트 변경
```yaml
api:
  port: 8001
```

#### 3. 음악 기능 안됨
```
⚠️ Spotify API 키 없음
```
**해결**: Spotify Developer에서 API 키 발급

#### 4. AI 기능 제한
```
⚠️ Serena 서버 연결 실패
```
**해결**: 로컬 AI 기능만 사용됨 (정상)

### 로그 확인
```bash
# 로그 파일 위치
tail -f logs/tikbot.log
```

## 📊 기능별 사용법

### 🎵 음악 시스템
```
!music 아이유 - 좋은날     # 곡 검색 요청
!music https://spotify.com/...  # Spotify URL
!queue                    # 대기열 확인
!skip                     # 곡 스킵
```

### 🤖 AI 시스템
```
!ai 오늘 날씨 어때?        # AI에게 질문
!insights                # 방송 인사이트
!analytics               # 상세 분석
```

### 📊 Analytics
- **실시간 데이터**: 참여도, 시청자 수, 성장률
- **SQLite 저장**: 모든 방송 데이터 영구 보관
- **시각화**: Plotly 차트, 실시간 업데이트

## 🎯 성능 최적화

### 메모리 사용량 줄이기
```yaml
analytics:
  cache_duration: 30      # 캐시 시간 단축
  collector:
    buffer_size: 50       # 버퍼 크기 축소
```

### CPU 사용량 줄이기
```yaml
features:
  tts_enabled: false      # TTS 비활성화
  overlay_enabled: false  # 오버레이 비활성화
```

## 🆘 지원 및 문서

### 추가 문서
- `FEATURES_ROADMAP.md` - 전체 기능 로드맵
- `README.md` - 프로젝트 개요
- `start.md` - 원본 개발 가이드

### 버그 리포트
GitHub Issues에 문제 신고: [GitHub Repository]

---

## 🎉 축하합니다!

TikBot이 성공적으로 실행되었습니다! 이제 다음을 즐기세요:

- ✅ **완전 무료** TikTok Live 자동화
- ✅ **AI 기반** 지능형 채팅 봇
- ✅ **실시간 분석** 대시보드
- ✅ **음악 통합** (Spotify + YouTube)
- ✅ **프로 수준** OBS 오버레이

**🚀 즐거운 방송 되세요!** 🎊
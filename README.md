# TikBot 🤖

**안정적이고 빠른 TikTok Live 자동화 봇** - Serena AI와 통합된 Python 기반 챗봇

## ✨ 주요 기능

### 🚀 **핵심 기능** (Phase 1 - 완료)
- 🎯 **실시간 채팅 수신**: TikTok Live 채팅을 실시간으로 모니터링
- 🤖 **자동 응답**: 키워드 기반 지능형 자동 응답 시스템
- ⚡ **명령어 처리**: 사용자 정의 명령어 처리 (`!help`, `!info`, `!time`, `!tts` 등)
- 🎁 **선물 & 팔로우 감지**: 선물, 팔로우, 좋아요 등 모든 이벤트 처리
- 🛡️ **스팸 필터링**: 지능형 스팸 메시지 자동 차단
- 📊 **실시간 통계**: 방송 통계 및 분석 데이터
- 🔗 **API 서버**: REST API로 외부 연동 가능
- 🔊 **TTS 기능**: 채팅 음성 읽기 (pyttsx3, gTTS 지원)

### 🎮 **예정 기능** (개발 중)
- 🎲 **Interactive Games**: 룰렛, 슬롯머신, 숫자맞추기 등
- 🎵 **Music Integration**: Spotify 연동 음악 요청
- 🎨 **Advanced Overlays**: 실시간 목표 달성 바, 리더보드
- 🤖 **AI Integration**: Serena 기반 지능형 대화
- 🔊 **Sound Alerts**: 이벤트별 효과음

## 🚀 빠른 시작

### 1. 설치

```bash
# 프로젝트 클론
git clone <repository-url>
cd tikbot

# 의존성 설치
uv sync

# 또는 pip 사용
pip install -e .
```

### 2. 설정

```yaml
# config.yaml 편집
tiktok:
  username: "your_tiktok_username"  # 실제 TikTok 사용자명으로 변경

features:
  auto_response: true      # 자동 응답 활성화
  command_processing: true # 명령어 처리 활성화
  spam_filter: true        # 스팸 필터 활성화
```

### 3. 실행

```bash
# 봇만 실행
uv run tikbot

# API 서버와 함께 실행
uv run tikbot --api

# 또는 Python 직접 실행
python -m tikbot.main
```

## 📖 사용법

### 기본 명령어

- `!help` - 사용 가능한 명령어 목록
- `!info` - 봇 정보 표시
- `!time` - 현재 방송 시간
- `!stats` - 방송 통계 정보
- `!tts 메시지` - 메시지를 음성으로 읽기
- `!commands` - 모든 명령어 목록

### 자동 응답

봇은 다음과 같은 키워드에 자동으로 응답합니다:

- **"안녕"** → "안녕하세요! 👋", "반가워요!", "환영합니다! 🎉"
- **"고마워"** → "천만에요! 😊", "도움이 되어서 기뻐요!", "언제든지요! ✨"
- **"bye"** → "안녕히 가세요! 👋", "또 봐요!", "수고하셨어요! 🙏"

## ⚙️ 고급 설정

### TTS (음성 읽기) 설정

```yaml
tts:
  engine: "pyttsx3"        # TTS 엔진
  voice_rate: 150          # 음성 속도
  voice_volume: 0.8        # 음성 볼륨
  language: "ko"           # 언어
```

### 오버레이 설정

```yaml
overlay:
  width: 800
  height: 600
  chat_font_size: 16
  max_messages: 20
  background_color: "rgba(0,0,0,0.7)"
  text_color: "#FFFFFF"
```

### API 서버

봇과 함께 REST API 서버를 실행하여 외부 애플리케이션과 연동할 수 있습니다:

```bash
tikbot --api
```

API 엔드포인트:
- `GET /api/stats` - 봇 통계
- `GET /api/events` - 최근 이벤트 목록
- `POST /api/commands` - 명령어 추가/수정
- `GET /health` - 헬스 체크

## 🛠️ 개발 및 확장

### Serena AI 통합

이 프로젝트는 [Serena](https://github.com/oraios/serena) AI 코딩 어시스턴트와 완벽하게 통합됩니다:

```bash
# Serena MCP 서버 시작
cd serena
uv run serena start-mcp-server

# Claude Desktop이나 다른 MCP 클라이언트에서 사용
```

### 커스텀 이벤트 핸들러

```python
from tikbot import TikBot
from tikbot.core.events import EventType

# 봇 인스턴스 생성
bot = TikBot(config)

# 커스텀 이벤트 핸들러 등록
@bot.event_handler.on(EventType.COMMENT)
async def my_comment_handler(event):
    print(f"새 댓글: {event.comment}")

# 봇 시작
await bot.start()
```

## 📊 아키텍처

```
tikbot/
├── src/tikbot/
│   ├── core/           # 핵심 봇 로직
│   │   ├── bot.py      # 메인 봇 클래스
│   │   ├── config.py   # 설정 관리
│   │   └── events.py   # 이벤트 시스템
│   ├── api/            # REST API 서버
│   ├── tts/            # TTS 기능
│   ├── overlay/        # 오버레이 기능
│   └── main.py         # 메인 엔트리포인트
├── config.yaml         # 봇 설정 파일
├── templates/          # 웹 템플릿
└── static/            # 정적 파일
```

## 🔧 문제 해결

### 연결 문제

1. TikTok 사용자명이 정확한지 확인
2. 네트워크 연결 상태 확인
3. TikTok Live가 활성화되어 있는지 확인

### 성능 최적화

- `config.yaml`에서 불필요한 기능 비활성화
- 스팸 필터 키워드 최적화
- 로그 레벨 조정 (`DEBUG` → `INFO`)

## 📝 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

## 🤝 기여

1. Fork 후 새 브랜치 생성
2. 기능 개발 또는 버그 수정
3. 테스트 추가
4. Pull Request 제출

## 🔗 관련 링크

- [TikTokLive Python Library](https://github.com/isaackogan/TikTokLive)
- [Serena AI Assistant](https://github.com/oraios/serena)
- [TikTok Developers](https://developers.tiktok.com)

---

**TikBot**으로 더 스마트하고 효율적인 TikTok Live 방송을 만들어보세요! 🚀
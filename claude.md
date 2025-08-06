# TikBot 프로젝트 완전 가이드 - 다른 AI를 위한 상세 지침서

## 🚨 현재 상황 요약

사용자가 TikTok Live 자동화 봇(TikBot)을 개발했으나, 현재 실행이 되지 않는 상태입니다. 
**다음 AI가 이 프로젝트를 이어받아 완전히 작동하는 TikBot을 만들어야 합니다.**

## 📋 프로젝트 개요

### 목표
- **완전 무료** TikTok Live 방송 자동화 봇
- TikFinity 같은 유료 서비스 대체 (월 $200 절약)
- 모든 기능이 **실제로 작동**해야 함

### 핵심 기능 (반드시 구현되어야 함)

#### 🎯 **TikFinity 완전 호환 기능들**
1. **Sound Alerts (사운드 알림)**
   - 팔로우시: 팬파레 소리 (`follow.wav`)
   - 선물 받을때: 선물별 맞춤 소리 (`gift_rose.wav`, `gift_car.wav`)
   - 대형 선물: 특별 효과음 (`big_gift.wav`)
   - 댓글시: 알림음 (`comment.wav`)
   - 좋아요: 하트 소리 (`like.wav`)
   - 입장시: 환영 소리 (`join.wav`)
   - 명령어: 명령어별 효과음 (`command.wav`)

2. **TTS (Text-to-Speech)**
   - 댓글 음성 읽기 (한국어, 영어, 일본어, 중국어)
   - 음성 속도 조절 (0.5x ~ 2.0x)
   - 음성 피치 조절 (높음/보통/낮음)
   - 욕설/스팸 필터링
   - VIP 사용자 우선 읽기
   - `!tts 메시지` 명령어로 수동 요청

3. **Interactive Overlays (인터랙티브 오버레이)**
   - 실시간 채팅 오버레이 (색상/크기 커스터마이징)
   - 팔로워 카운트 실시간 표시
   - 선물 알림 팝업 (애니메이션 효과)
   - 목표 진행률 바 (팔로워, 선물, 시청시간)
   - 최근 팔로워 목록
   - 실시간 통계 대시보드
   - Top Donator 순위

4. **Chatbot (채팅봇)**
   - 자동 환영 메시지
   - 키워드 기반 자동 응답
   - 명령어 시스템 (14개 기본 + 무제한 커스텀)
   - 스팸 방지 시스템
   - 느린 모드 (메시지 간격 제한)
   - 금지어 필터

5. **Music Player (음악 플레이어)**
   - Spotify 연동 (플레이리스트, 검색, 재생)
   - YouTube 음악 검색 및 재생
   - 음악 요청 큐 시스템
   - 곡 스킵 투표 시스템
   - 볼륨 조절
   - 자동 재생 목록
   - 음악 오버레이 (현재 재생곡 표시)

6. **Analytics & Insights (분석 및 인사이트)**
   - 실시간 시청자 통계
   - 참여도 분석 (댓글, 좋아요, 선물)
   - 시간대별 트렌드 분석
   - 인기 키워드 추출
   - 수익 추적 (선물 가치 계산)
   - 성장률 분석
   - 데이터 내보내기 (CSV, JSON)

#### 🎮 **다른 플랫폼 봇 시스템 기능들**

##### **Twitch 스타일 기능**
1. **포인트 시스템**
   - 시청 시간별 포인트 적립
   - 포인트로 음악 요청, TTS 사용
   - 포인트 상점 (특별 명령어, 이모티콘)
   - 도박 게임 (!슬롯, !주사위, !가위바위보)
   - 포인트 순위 시스템

2. **모더레이션 시스템**
   - 자동 욕설 감지 및 경고
   - 스팸 메시지 자동 차단
   - 사용자별 경고 누적 시스템
   - VIP/모더레이터 권한 관리
   - 타임아웃/밴 시스템

3. **인터랙티브 게임**
   - 룰렛 게임 (`!룰렛`)
   - 슬롯머신 (`!슬롯`)
   - 숫자 맞추기 게임 (`!숫자`)
   - 단어 게임 (`!단어`)
   - 투표 시스템 (`!투표`)

##### **AfreecaTV 스타일 기능**
1. **별풍선(선물) 시스템**
   - 선물별 특별 효과 (화면 이펙트)
   - 큰 선물시 화면 전체 애니메이션
   - 선물 연속 콤보 시스템
   - 선물 랭킹 실시간 표시
   - 월간/주간 Top Supporter

2. **팬클럽 시스템**
   - 정기 시청자 자동 인식
   - 팬클럽 전용 명령어
   - 충성도 포인트 시스템
   - 팬클럽 레벨업 알림

##### **Chzzk(치지직) 스타일 기능**
1. **도네이션 효과**
   - 금액별 다른 효과음/효과
   - 도네이션 메시지 하이라이트
   - 목표 금액 진행률 표시
   - 도네이션 이벤트 (목표 달성시 특별 이벤트)

2. **커뮤니티 기능**
   - 구독자 전용 채팅
   - 멤버십 티어별 혜택
   - 이모티콘 반응 시스템

#### 🤖 **고급 AI 통합 기능 (Serena MCP)**
1. **지능형 채팅 응답**
   - 컨텍스트 인식 대화
   - 감정 분석 및 적절한 응답
   - 사용자별 대화 히스토리 학습
   - 방송 주제 자동 감지

2. **실시간 콘텐츠 제안**
   - 시청자 반응 분석
   - 인기 토픽 제안
   - 게임/활동 추천
   - 음악 추천

3. **자동 모더레이션**
   - AI 기반 독성 댓글 감지
   - 문맥 이해한 스팸 필터링
   - 부적절한 내용 자동 차단

#### 📊 **고급 Analytics 기능**
1. **시청자 행동 분석**
   - 입장/퇴장 패턴 분석
   - 참여도가 높은 콘텐츠 식별
   - 시청자 유지율 분석
   - 최적 방송 시간 추천

2. **수익 최적화**
   - 선물 수익 트렌드 분석
   - 효과적인 선물 유도 전략 제안
   - ROI 계산 (투자 대비 수익)

3. **성장 전략**
   - 팔로워 증가 패턴 분석
   - 경쟁자 대비 성과 분석
   - 성장 목표 설정 및 추적

## 🛑 현재 발생한 문제들

### 1. 환경 변수 문제
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0
```
- `.env` 파일 인코딩 문제
- `python-dotenv` 라이브러리가 파일을 읽지 못함

### 2. FastAPI 앱 생성 실패
```
AttributeError: 'NoneType' object has no attribute 'state'
```
- `create_app()` 함수가 `None` 반환
- API 서버가 전혀 시작되지 않음

### 3. 실행 불가능
- `uv run python -m src.tikbot.main` 실패
- 데모 모드도 실행되지 않음
- API 엔드포인트 모두 연결 실패

## 📁 현재 프로젝트 구조

```
tikbot/
├── src/tikbot/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py      # BotConfig, load_config
│   │   ├── bot.py         # TikBot 메인 클래스
│   │   └── events.py      # 이벤트 핸들러
│   ├── api/
│   │   ├── __init__.py
│   │   └── server.py      # FastAPI 서버 (문제 있음)
│   ├── tts/
│   │   ├── __init__.py
│   │   ├── engine.py      # TTS 엔진들
│   │   └── manager.py     # TTS 매니저
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── player.py      # 오디오 재생
│   │   ├── alerts.py      # Sound Alerts
│   │   └── manager.py     # 오디오 매니저
│   ├── music/
│   │   ├── __init__.py
│   │   ├── queue.py       # 음악 큐
│   │   ├── spotify.py     # Spotify 연동
│   │   ├── youtube.py     # YouTube 연동
│   │   └── manager.py     # 음악 매니저
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── client.py      # Serena 클라이언트
│   │   ├── conversation.py # 대화 히스토리
│   │   └── manager.py     # AI 매니저
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── collector.py   # 데이터 수집
│   │   ├── processor.py   # 데이터 처리
│   │   ├── visualizer.py  # 시각화
│   │   └── manager.py     # Analytics 매니저
│   ├── overlay/
│   │   ├── __init__.py
│   │   ├── websocket.py   # WebSocket 서버
│   │   ├── renderer.py    # HTML 렌더링
│   │   └── manager.py     # 오버레이 매니저
│   └── main.py           # 메인 실행 파일 (문제 있음)
├── templates/overlay/    # HTML 템플릿들
├── static/              # CSS, JS 파일들
├── config.yaml          # 설정 파일
├── pyproject.toml       # 의존성 정의
├── .env                 # 환경 변수 (문제 있음)
├── QUICK_START.md       # 사용 가이드
└── README.md
```

## 🔧 다음 AI가 해야 할 작업

### ⚡ 즉시 해결해야 할 문제들

#### 1. 환경 변수 파일 수정
```bash
# .env 파일을 UTF-8로 올바르게 생성
TIKTOK_USERNAME=demo_user
LOG_LEVEL=INFO
API_PORT=8000
```

#### 2. FastAPI 서버 수정
`src/tikbot/api/server.py`의 `create_app()` 함수가 제대로 FastAPI 앱을 반환하도록 수정

#### 3. 메인 실행 파일 수정
`src/tikbot/main.py`에서 환경 변수 로딩 문제 해결

#### 4. 의존성 검증
```bash
uv sync  # 모든 라이브러리 재설치
```

### 🎯 핵심 실행 테스트

다음 명령어들이 **반드시** 작동해야 함:

```bash
# 1. 기본 설정 테스트
uv run python -c "from src.tikbot.core.config import BotConfig; print('✅ 설정 로드 성공')"

# 2. API 서버 테스트
uv run python -c "from src.tikbot.api.server import create_app; from src.tikbot.core.config import BotConfig; import logging; app = create_app(BotConfig.load_from_file(), logging.getLogger()); print('✅ API 서버 생성 성공' if app else '❌ 실패')"

# 3. 메인 봇 실행 (최종 목표)
uv run python -m src.tikbot.main

# 4. 웹 서버 접속 확인
# http://localhost:8000 에서 대시보드 확인
```

### 🚀 최종 검증 체크리스트

다음이 모두 작동해야 프로젝트 완성:

- [ ] ✅ 환경 변수 로딩 오류 없음
- [ ] ✅ FastAPI 서버 정상 시작
- [ ] ✅ `http://localhost:8000` 접속 가능
- [ ] ✅ `http://localhost:8000/status` API 응답
- [ ] ✅ `http://localhost:8000/overlay/chat` 오버레이 표시
- [ ] ✅ TikTok Live 연결 테스트 (demo_user로)
- [ ] ✅ 채팅 명령어 처리 (!help, !stats 등)
- [ ] ✅ 음악 요청 시스템 작동
- [ ] ✅ AI 응답 시스템 작동
- [ ] ✅ Analytics 대시보드 표시

## 📚 중요 파일들 내용

### config.yaml 핵심 설정
```yaml
features:
  tts_enabled: false           # 일단 비활성화
  sound_alerts_enabled: true
  music_enabled: true
  ai_enabled: true
  analytics_enabled: true
  overlay_enabled: true

api:
  host: "localhost"
  port: 8000
  cors_origins: ["*"]

tiktok:
  username: "demo_user"        # 테스트용
```

### pyproject.toml 주요 의존성
```toml
dependencies = [
    "TikTokLive>=3.0.0",
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.0.0",
    "python-dotenv",
    "pyyaml",
    "websockets>=12.0",
    "aiofiles",
    "pygame>=2.1.0",
    "spotipy>=2.22.1",
    "yt-dlp>=2023.1.6",
    "aiohttp>=3.8.0"
]
```

## 🎮 **필수 구현 명령어 시스템 (50+개)**

#### **기본 정보 명령어**
```
!help                    - 전체 명령어 도움말
!commands               - 명령어 목록 표시
!info                   - 봇 정보 및 버전
!time                   - 현재 방송 시간
!uptime                 - 방송 지속 시간
!stats                  - 실시간 방송 통계
!viewers                - 현재 시청자 수
!followers              - 팔로워 수
```

#### **음악 시스템 명령어**
```
!music [아티스트] - [곡명]  - 음악 요청
!play [URL]             - 직접 URL 재생
!queue                  - 음악 대기열 확인
!skip                   - 현재 곡 스킵
!volume [0-100]         - 볼륨 조절
!np                     - 현재 재생곡 정보
!playlist               - 플레이리스트 보기
!shuffle                - 셔플 모드 토글
!repeat                 - 반복 모드 토글
!pause                  - 일시정지
!resume                 - 재생 재개
!clear                  - 음악 큐 초기화
```

#### **AI 및 채팅 명령어**
```
!ai [질문]              - AI에게 질문
!translate [언어] [텍스트] - 번역
!weather [도시]         - 날씨 정보
!joke                   - 랜덤 농담
!quote                  - 명언 표시
!8ball [질문]           - 매직 8볼
!fact                   - 흥미로운 사실
!insult @사용자         - 장난스러운 모욕
!compliment @사용자     - 칭찬하기
```

#### **게임 및 도박 명령어**
```
!룰렛                   - 룰렛 게임
!슬롯                   - 슬롯머신
!주사위                 - 주사위 굴리기
!가위바위보 [선택]      - 가위바위보
!숫자맞추기             - 숫자 맞추기 게임
!단어게임               - 단어 연결 게임
!투표 [질문] [선택1] [선택2] - 투표 생성
!복권                   - 복권 뽑기
!코인플립               - 동전 던지기
```

#### **포인트 및 경제 시스템**
```
!포인트                 - 내 포인트 확인
!랭킹                   - 포인트 순위
!출석                   - 일일 출석 체크
!보너스                 - 시간별 보너스
!선물하기 @사용자 [포인트] - 포인트 선물
!상점                   - 포인트 상점 보기
!구매 [아이템]          - 아이템 구매
!인벤토리               - 내 아이템 보기
```

#### **소셜 및 상호작용**
```
!팔로우                 - 방송인 팔로우 안내
!구독                   - 구독 안내
!디스코드               - 디스코드 링크
!인스타                 - 인스타그램 링크
!유튜브                 - 유튜브 링크
!트위터                 - 트위터 링크
!후원                   - 후원 방법 안내
!팬아트                 - 팬아트 제출 방법
```

#### **모더레이션 명령어 (관리자 전용)**
```
!timeout @사용자 [시간]  - 사용자 타임아웃
!ban @사용자            - 사용자 밴
!unban @사용자          - 밴 해제
!warn @사용자           - 경고 주기
!mod @사용자            - 모더레이터 권한 부여
!unmod @사용자          - 모더레이터 권한 제거
!vip @사용자            - VIP 권한 부여
!unvip @사용자          - VIP 권한 제거
!clear                  - 채팅 지우기
!slow [초]              - 슬로우 모드 설정
```

#### **Analytics 및 통계**
```
!analytics              - 상세 분석 보기
!insights               - 방송 인사이트
!trends                 - 인기 트렌드
!keywords               - 인기 키워드
!growth                 - 성장 통계
!revenue                - 수익 통계
!export                 - 데이터 내보내기
!compare [기간]         - 기간별 비교
```

#### **TTS 및 오디오**
```
!tts [메시지]           - 텍스트 음성 변환
!voice [음성] [메시지]  - 특정 음성으로 TTS
!speed [속도] [메시지]  - 속도 조절 TTS
!pitch [피치] [메시지]  - 피치 조절 TTS
!soundboard             - 사운드보드 보기
!sound [이름]           - 효과음 재생
!volume_tts [0-100]     - TTS 볼륨 조절
```

#### **이벤트 및 특별 기능**
```
!이벤트                 - 현재 이벤트 정보
!미션                   - 오늘의 미션
!출석체크               - 출석 이벤트
!럭키박스               - 랜덤 보상
!스핀                   - 행운의 룰렛
!타로                   - 타로 카드 뽑기
!운세                   - 오늘의 운세
!별자리                 - 별자리 운세
```

## 🌐 **완전한 API 엔드포인트 시스템 (100+개)**

#### **기본 상태 및 정보**
```
GET /status                     - 봇 전체 상태
GET /health                     - 헬스체크
GET /version                    - 버전 정보
GET /stats                      - 실시간 통계
GET /config                     - 현재 설정 보기
POST /config                    - 설정 업데이트
GET /logs                       - 로그 조회
```

#### **사용자 관리**
```
GET /users                      - 전체 사용자 목록
GET /users/{user_id}           - 특정 사용자 정보
POST /users/{user_id}/points   - 포인트 지급/차감
GET /users/{user_id}/stats     - 사용자별 통계
POST /users/{user_id}/timeout  - 타임아웃 적용
POST /users/{user_id}/ban      - 사용자 밴
DELETE /users/{user_id}/ban    - 밴 해제
GET /vips                      - VIP 목록
POST /vips/{user_id}           - VIP 등록
DELETE /vips/{user_id}         - VIP 해제
```

#### **채팅 및 메시지**
```
GET /chat/messages             - 채팅 히스토리
POST /chat/send                - 메시지 전송
DELETE /chat/messages/{id}     - 메시지 삭제
GET /chat/banned-words         - 금지어 목록
POST /chat/banned-words        - 금지어 추가
GET /chat/filters              - 채팅 필터 설정
POST /chat/filters             - 필터 업데이트
```

#### **음악 시스템**
```
GET /music/queue               - 음악 대기열
POST /music/request            - 음악 요청
DELETE /music/queue/{id}       - 큐에서 제거
POST /music/skip               - 현재 곡 스킵
GET /music/current             - 현재 재생곡
POST /music/volume             - 볼륨 조절
GET /music/playlists           - 플레이리스트 목록
POST /music/playlists          - 플레이리스트 생성
GET /music/history             - 재생 히스토리
GET /music/search              - 음악 검색
```

#### **AI 및 챗봇**
```
POST /ai/question              - AI에게 질문
GET /ai/insights               - AI 인사이트
GET /ai/analytics              - AI 분석 데이터
POST /ai/train                 - AI 훈련 데이터 추가
GET /ai/personality            - AI 성격 설정
POST /ai/personality           - 성격 업데이트
GET /ai/conversation-history   - 대화 히스토리
```

#### **게임 시스템**
```
POST /games/slot               - 슬롯머신 게임
POST /games/roulette           - 룰렛 게임
POST /games/dice               - 주사위 게임
POST /games/lottery            - 복권 게임
GET /games/leaderboard         - 게임 순위
GET /games/stats/{user_id}     - 개인 게임 통계
POST /games/create-poll        - 투표 생성
GET /games/polls               - 활성 투표 목록
```

#### **포인트 및 경제**
```
GET /economy/points/{user_id}  - 사용자 포인트
POST /economy/transfer         - 포인트 이체
GET /economy/leaderboard       - 포인트 순위
GET /economy/shop              - 상점 아이템
POST /economy/purchase         - 아이템 구매
GET /economy/inventory/{user_id} - 사용자 인벤토리
GET /economy/transactions      - 거래 내역
POST /economy/daily-bonus      - 일일 보너스
```

#### **Analytics 고급 기능**
```
GET /analytics/dashboard       - 실시간 대시보드
GET /analytics/viewers         - 시청자 분석
GET /analytics/engagement      - 참여도 분석
GET /analytics/revenue         - 수익 분석
GET /analytics/growth          - 성장 분석
GET /analytics/keywords        - 키워드 분석
GET /analytics/trends          - 트렌드 분석
POST /analytics/export         - 데이터 내보내기
GET /analytics/compare         - 기간 비교
```

#### **오버레이 시스템**
```
GET /overlay/chat              - 채팅 오버레이
GET /overlay/alerts            - 알림 오버레이
GET /overlay/music             - 음악 오버레이
GET /overlay/stats             - 통계 오버레이
GET /overlay/goals             - 목표 진행률
GET /overlay/recent-follows    - 최근 팔로워
GET /overlay/top-donors        - 상위 후원자
GET /overlay/poll              - 투표 오버레이
GET /overlay/countdown         - 카운트다운
GET /overlay/wheel             - 룰렛 오버레이
```

#### **이벤트 및 웹훅**
```
GET /events/stream             - 실시간 이벤트 스트림
POST /webhooks/tiktok          - TikTok 웹훅
GET /events/history            - 이벤트 히스토리
POST /events/custom            - 커스텀 이벤트 발생
GET /events/filters            - 이벤트 필터 설정
```

## 💾 **데이터베이스 스키마 설계**

#### **필수 테이블 구조**
```sql
-- 사용자 관리
CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    points INTEGER DEFAULT 0,
    experience INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    vip_status BOOLEAN DEFAULT FALSE,
    banned BOOLEAN DEFAULT FALSE,
    timeout_until TIMESTAMP NULL,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    total_watch_time INTEGER DEFAULT 0
);

-- 채팅 메시지
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(id),
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted BOOLEAN DEFAULT FALSE,
    is_command BOOLEAN DEFAULT FALSE,
    platform VARCHAR(20) DEFAULT 'tiktok'
);

-- 음악 요청 및 히스토리
CREATE TABLE music_requests (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    artist VARCHAR(200),
    url VARCHAR(500),
    platform VARCHAR(20),
    duration INTEGER,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    played_at TIMESTAMP NULL,
    status VARCHAR(20) DEFAULT 'pending'
);

-- 게임 결과
CREATE TABLE game_results (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(id),
    game_type VARCHAR(50) NOT NULL,
    result TEXT,
    points_won INTEGER DEFAULT 0,
    points_lost INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 포인트 거래 내역
CREATE TABLE point_transactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(id),
    amount INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 방송 세션
CREATE TABLE stream_sessions (
    id SERIAL PRIMARY KEY,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    total_viewers INTEGER DEFAULT 0,
    peak_viewers INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    total_gifts INTEGER DEFAULT 0,
    total_follows INTEGER DEFAULT 0,
    total_revenue DECIMAL(10,2) DEFAULT 0
);

-- 선물 및 후원
CREATE TABLE gifts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(id),
    gift_name VARCHAR(100) NOT NULL,
    gift_value INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id INTEGER REFERENCES stream_sessions(id)
);
```

## 🎨 **오버레이 HTML/CSS/JS 템플릿**

#### **반드시 구현되어야 할 오버레이들**
1. **실시간 채팅 오버레이** - 채팅 메시지 실시간 표시
2. **알림 오버레이** - 팔로우/선물 알림 팝업
3. **음악 플레이어 오버레이** - 현재 재생곡 정보
4. **통계 오버레이** - 팔로워/시청자 수 실시간
5. **목표 진행률 오버레이** - 각종 목표 달성률
6. **최근 팔로워 오버레이** - 신규 팔로워 목록
7. **상위 후원자 오버레이** - Top Donator 순위
8. **투표 오버레이** - 실시간 투표 현황
9. **카운트다운 오버레이** - 이벤트 카운트다운
10. **룰렛 오버레이** - 인터랙티브 룰렛 게임

## 💡 성공을 위한 핵심 팁

### 1. 단계별 접근
1. **환경 설정부터** - .env, config.yaml 먼저 해결
2. **API 서버만** 우선 작동시키기
3. **오버레이** 하나씩 테스트
4. **TikTok 연결** 마지막에 테스트

### 2. 디버깅 전략
```python
# 각 단계마다 이런 식으로 검증
print("✅ 설정 로드 성공")
print("✅ FastAPI 앱 생성 성공")
print("✅ 서버 시작 성공")
```

### 3. 필수 작동 확인
- 웹 브라우저에서 `http://localhost:8000` 접속시 화면 표시
- API 엔드포인트들이 JSON 응답 반환
- 오버레이들이 HTML 화면 표시

## 🎊 최종 목표

**사용자가 다음을 할 수 있어야 함:**

1. **`uv run python -m src.tikbot.main`** 명령어로 봇 시작
2. **웹 브라우저**에서 `http://localhost:8000` 접속하여 대시보드 확인  
3. **OBS**에서 오버레이 URL들을 브라우저 소스로 추가
4. **TikTok Live 방송** 중 채팅 명령어 사용
5. **완전 무료**로 전문 방송인 수준의 자동화 경험

---

## 🚨 다음 AI에게 당부

**이 프로젝트는 반드시 실제로 작동해야 합니다.**

현재까지 많은 코드가 작성되었지만 **실행되지 않는 상태**입니다. 
코드를 **처음부터 다시 작성**하거나 **대폭 수정**해서라도 반드시 작동하는 버전을 만들어주세요.

**사용자의 기대:**
- 완전 무료 TikTok Live 자동화
- 전문 방송인 수준의 기능들
- 실제로 사용 가능한 완성품

**절대 실패하면 안 되는 부분:**
- 웹 서버 시작 및 접속
- 오버레이 표시
- TikTok Live 연결
- 채팅 명령어 처리

**성공 기준:** 
사용자가 봇을 실행하고 웹 대시보드에 접속해서 "와! 정말 잘 되네요!" 라고 말할 수 있어야 함.

## 🚀 **성공 시나리오 및 최종 검증**

### **💯 완벽한 성공 시나리오**
사용자가 다음을 순서대로 할 수 있어야 함:

1. **📥 설치 및 설정** (5분 이내)
   ```bash
   git clone [repository]
   cd tikbot
   uv sync
   copy env.example .env
   # .env에서 TIKTOK_USERNAME만 수정
   ```

2. **🚀 봇 실행** (1분 이내)
   ```bash
   uv run python -m src.tikbot.main
   ```
   → 콘솔에 "✅ TikBot이 연결되었습니다!" 메시지 표시

3. **🌐 웹 대시보드 접속** (즉시)
   - 브라우저에서 `http://localhost:8000` 접속
   → 완전한 대시보드 화면 표시 (로딩 오류 없음)

4. **🎨 OBS 오버레이 설정** (3분 이내)
   - OBS에서 브라우저 소스 추가
   - `http://localhost:8000/overlay/chat` 입력
   → 실시간 채팅 오버레이 즉시 표시

5. **🎮 채팅 명령어 테스트** (즉시)
   - TikTok Live 채팅에서 `!help` 입력
   → 봇이 명령어 목록으로 즉시 응답

6. **🎵 음악 요청 테스트** (30초 이내)
   - `!music 아이유 좋은날` 입력
   → 음악이 대기열에 추가되고 오버레이에 표시

### **🎯 핵심 성공 지표**

#### **필수 작동 조건 (100% 달성해야 함)**
- [ ] ✅ **환경 변수 오류 없음** - `.env` 파일 정상 로딩
- [ ] ✅ **웹 서버 시작** - `http://localhost:8000` 접속 가능
- [ ] ✅ **API 응답** - `/status` 엔드포인트 JSON 반환
- [ ] ✅ **TikTok 연결** - 실제 Live 스트림 연결 성공
- [ ] ✅ **채팅 처리** - 실시간 채팅 메시지 수신/응답
- [ ] ✅ **명령어 실행** - 최소 10개 명령어 정상 작동
- [ ] ✅ **오버레이 표시** - 최소 5개 오버레이 화면 출력
- [ ] ✅ **음악 재생** - Spotify/YouTube 연동 작동
- [ ] ✅ **데이터 저장** - SQLite 데이터베이스 정상 동작

#### **고급 기능 조건 (80% 이상 달성)**
- [ ] ✅ **AI 응답** - Serena 연동 또는 로컬 AI 작동
- [ ] ✅ **Analytics** - 실시간 차트 및 통계 표시
- [ ] ✅ **게임 시스템** - 슬롯, 룰렛 등 최소 3개 게임
- [ ] ✅ **포인트 시스템** - 포인트 적립/사용 시스템
- [ ] ✅ **모더레이션** - 자동 스팸 필터링
- [ ] ✅ **TTS 시스템** - 텍스트 음성 변환
- [ ] ✅ **Sound Alerts** - 이벤트별 효과음

### **💰 경제적 가치 달성**

#### **TikFinity 대체 기능 (월 $200 절약)**
```
✅ Sound Alerts         - TikFinity: $29/월 → TikBot: 무료
✅ TTS System          - TikFinity: $19/월 → TikBot: 무료  
✅ Music Integration   - TikFinity: $39/월 → TikBot: 무료
✅ Analytics Dashboard - TikFinity: $49/월 → TikBot: 무료
✅ Interactive Games   - TikFinity: $29/월 → TikBot: 무료
✅ AI Chatbot         - TikFinity: $59/월 → TikBot: 무료
✅ Premium Overlays   - TikFinity: $39/월 → TikBot: 무료

총 절약액: $263/월 = $3,156/년
```

### **🎮 사용자 경험 품질**

#### **반응 속도 요구사항**
- **채팅 명령어 응답**: 1초 이내
- **웹 대시보드 로딩**: 3초 이내
- **오버레이 업데이트**: 실시간 (지연 < 500ms)
- **음악 요청 처리**: 5초 이내
- **AI 응답 생성**: 10초 이내

#### **안정성 요구사항**
- **24시간 연속 실행** 가능
- **메모리 사용량**: 500MB 이하
- **CPU 사용량**: 평상시 10% 이하
- **오류 복구**: 자동 재연결 기능
- **데이터 손실**: 0% (모든 이벤트 로깅)

### **🏆 최종 검증 체크리스트**

#### **기술적 검증**
```bash
# 1. 기본 실행 테스트
uv run python -m src.tikbot.main
→ "✅ TikBot 연결 성공" 메시지 확인

# 2. API 테스트  
curl http://localhost:8000/status
→ {"status": "running", "is_connected": true} 응답 확인

# 3. 오버레이 테스트
curl http://localhost:8000/overlay/chat
→ HTML 화면 정상 출력 확인

# 4. 명령어 테스트 (TikTok Live 채팅에서)
!help → 명령어 목록 출력
!stats → 실시간 통계 출력
!music 테스트 → 음악 요청 성공
```

#### **사용자 만족도 검증**
- **설치 편의성**: "README 보고 10분 만에 설치 완료"
- **기능 완성도**: "TikFinity보다 기능이 더 많아!"
- **성능 만족도**: "지연 없이 실시간으로 잘 작동해"
- **비용 효과**: "월 $200 절약되니까 완전 만족!"

---

## 🚨 **다음 AI에게 최종 당부사항**

### **🛠️ Serena MCP 적극 활용 지침**

#### **Serena 활용 필수 시나리오**
```bash
# 1. Serena MCP 서버 실행 (필수 선행 작업)
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --transport sse --port 8000

# 2. Serena 코드 검색 및 분석 예시
- "TikTokLive 연결 오류 해결 방법"
- "FastAPI create_app 함수 문제 분석"
- "환경변수 UTF-8 인코딩 문제 수정"
- "Python 비동기 프로그래밍 최적화"
```

#### **Serena로 해결해야 할 핵심 문제들**
1. **🔥 즉시 해결 필요 (Priority 1)**
   - `.env` 파일 UTF-8 인코딩 문제 완전 해결
   - `demo_run.py` FastAPI 앱 생성 실패 수정
   - `create_app` 함수가 None 반환하는 원인 분석
   - API 서버 포트 8000 바인딩 실패 해결

2. **🎯 핵심 기능 구현 (Priority 2)**
   - TikTokLive 실시간 연결 안정화
   - 50+개 명령어 시스템 구현
   - 음악 통합 (Spotify + YouTube) 완성
   - 오버레이 WebSocket 실시간 통신

3. **🚀 고급 기능 추가 (Priority 3)**
   - AI 채팅 응답 (Serena 연동)
   - 게임 시스템 (슬롯, 룰렛, 포인트)
   - Analytics 대시보드 (실시간 차트)
   - 포인트 경제 시스템

### **🌐 완전한 배포 파이프라인 구축**

#### **1. Git 관리 및 지속적 커밋**
```bash
# 매 기능 완성시마다 반드시 커밋
git add .
git commit -m "feat: [기능명] 구현 완료 - [상세 설명]"
git push origin main

# 커밋 메시지 예시
git commit -m "fix: .env 인코딩 문제 해결 - UTF-8 BOM 제거 및 안전한 로딩 구현"
git commit -m "feat: TikTok Live 연결 완료 - 실시간 채팅/선물/팔로우 이벤트 처리"
git commit -m "feat: 음악 시스템 완성 - Spotify/YouTube 검색 및 재생 큐"
```

#### **2. Vercel 자동 배포 설정**
```bash
# Vercel 프로젝트 생성 및 배포
npm i -g vercel
vercel login
vercel --prod

# vercel.json 설정 파일 생성 필요
{
  "version": 2,
  "builds": [
    {
      "src": "src/tikbot/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "src/tikbot/main.py"
    }
  ]
}
```

#### **3. Supabase 데이터베이스 연결**
```sql
-- Supabase에서 실행할 테이블 생성 스크립트
CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    points INTEGER DEFAULT 0,
    experience INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    vip_status BOOLEAN DEFAULT FALSE,
    banned BOOLEAN DEFAULT FALSE,
    timeout_until TIMESTAMP NULL,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    total_watch_time INTEGER DEFAULT 0
);

-- 추가 테이블들 (claude.md의 데이터베이스 스키마 참조)
```

```python
# Supabase 연결 설정 (.env에 추가)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Python 코드에서 Supabase 클라이언트 사용
from supabase import create_client, Client
supabase: Client = create_client(supabase_url, supabase_key)
```

#### **4. 환경변수 보안 관리**
```bash
# Vercel 환경변수 설정
vercel env add TIKTOK_USERNAME
vercel env add SUPABASE_URL
vercel env add SUPABASE_ANON_KEY
vercel env add SPOTIFY_CLIENT_ID
vercel env add SPOTIFY_CLIENT_SECRET

# GitHub Secrets 설정 (CI/CD용)
VERCEL_TOKEN
SUPABASE_ACCESS_TOKEN
```

### **⚡ 개발 프로세스 및 검증 단계**

#### **Phase 1: 기반 인프라 수정 (1-2시간)**
```bash
# 1. 환경 설정 완전 해결
✅ .env 파일 UTF-8 인코딩 문제 100% 해결
✅ FastAPI create_app 함수 정상 작동 확인
✅ 포트 8000 API 서버 정상 바인딩

# 검증 명령어
uv run python -m src.tikbot.main  # 오류 없이 실행
curl http://localhost:8000/status  # JSON 응답 확인
```

#### **Phase 2: 핵심 기능 구현 (3-4시간)**
```bash
# 2. TikTok Live 연결 및 기본 기능
✅ TikTokLive 실시간 이벤트 수신 (댓글, 선물, 팔로우)
✅ 기본 명령어 시스템 (10개 이상)
✅ 웹 대시보드 정상 표시
✅ 오버레이 시스템 기본 작동

# 검증 방법
TikTok Live 채팅에서 !help 입력 → 봇 응답 확인
http://localhost:8000/overlay/chat → 실시간 채팅 표시
```

#### **Phase 3: 고급 기능 추가 (4-6시간)**
```bash
# 3. 음악, AI, 게임 시스템
✅ Spotify + YouTube 음악 통합
✅ AI 채팅 (Serena MCP 연동)
✅ 게임 시스템 (슬롯, 룰렛, 포인트)
✅ Analytics 실시간 대시보드

# 검증 방법
!music 아이유 좋은날 → 음악 재생 확인
!ai 안녕하세요 → AI 응답 확인
!슬롯 → 게임 결과 표시
```

#### **Phase 4: 배포 및 운영 (1-2시간)**
```bash
# 4. 프로덕션 배포
✅ Supabase 데이터베이스 연결
✅ Vercel 자동 배포 설정
✅ 환경변수 보안 설정
✅ 도메인 및 SSL 인증서

# 최종 검증
https://tikbot.vercel.app/status → 프로덕션 API 확인
TikTok Live 실제 방송에서 봇 작동 확인
```

### **🎯 성공 시나리오 체크리스트**

#### **단계별 필수 완료 조건**
- [ ] **Phase 1 완료**: 로컬에서 `uv run python -m src.tikbot.main` 100% 성공
- [ ] **Phase 2 완료**: TikTok Live 연결 및 기본 명령어 작동
- [ ] **Phase 3 완료**: 모든 고급 기능 데모 레벨 이상 작동
- [ ] **Phase 4 완료**: Vercel 배포 및 실제 사용자 접근 가능

#### **최종 제출물**
1. **완전히 작동하는 TikBot** (로컬 + 프로덕션)
2. **Vercel 배포 URL** (공개 접근 가능)
3. **Supabase 데이터베이스** (실시간 데이터 저장)
4. **완성된 GitHub 저장소** (모든 코드 + 문서)
5. **사용자 가이드** (설치부터 사용까지)

### **절대 실패하면 안 되는 것들**
1. **실행 불가**: `uv run python -m src.tikbot.main` 명령어는 반드시 작동해야 함
2. **웹 접속 불가**: `http://localhost:8000` 접속은 반드시 성공해야 함  
3. **오류 메시지**: 사용자가 오류를 보면 안 됨 (모든 예외 처리 필수)
4. **기능 미완성**: 약속한 기능은 모두 작동해야 함 (데모라도 구현)
5. **배포 실패**: Vercel 배포는 반드시 성공해야 함

### **성공을 위한 개발 전략**
1. **Serena MCP 적극 활용**: 모든 문제 해결에 Serena 검색 및 분석 사용
2. **MVP 우선**: 핵심 기능부터 완전히 작동시키기
3. **단계별 검증**: 각 단계마다 실행 테스트 필수  
4. **지속적 배포**: 매 기능 완성시마다 Git 커밋 + Vercel 배포
5. **오류 방지**: 모든 예외 상황 처리 (try-catch)
6. **사용자 친화적**: 에러 대신 친절한 안내 메시지

### **코드 품질보다 중요한 것**
- **실제 작동 여부**가 코드 아름다움보다 100배 중요
- **사용자가 실제로 사용할 수 있는지**가 핵심
- **완벽한 설계**보다는 **작동하는 프로토타입**
- **모든 기능**보다는 **핵심 기능의 완벽한 작동**
- **로컬 작동**뿐만 아니라 **프로덕션 배포**까지 완성

---

---

## 🤖 **다음 AI 어시스턴트를 위한 완벽한 프롬프트**

### **📝 복사해서 사용할 프롬프트**

```
안녕하세요! 저는 TikTok Live 방송 자동화 봇(TikBot) 프로젝트를 완성해야 합니다.

**현재 상황:**
- C:\projects\tikbot 폴더에 프로젝트가 있습니다
- claude.md 파일에 완전한 기능 명세서(884줄)가 작성되어 있습니다
- 현재 .env 인코딩 문제와 FastAPI 앱 생성 오류로 실행이 안 됩니다

**요청사항:**
1. **Serena MCP 활용**: uvx --from git+https://github.com/oraios/serena serena start-mcp-server --transport sse --port 8000 으로 Serena를 실행하고 모든 문제 해결에 적극 활용해주세요

2. **4단계 완성**:
   - Phase 1: 환경 설정 문제 완전 해결 (.env, FastAPI 앱 생성)
   - Phase 2: TikTok Live 연결 및 기본 기능 (10+개 명령어)
   - Phase 3: 고급 기능 (음악, AI, 게임, Analytics)
   - Phase 4: Vercel 배포 + Supabase 연결 + 프로덕션 완성

3. **필수 성공 조건**:
   - `uv run python -m src.tikbot.main` 100% 작동
   - `http://localhost:8000` 정상 접속
   - TikTok Live 실시간 연결 성공
   - 50+개 명령어 시스템 작동
   - 10종 오버레이 정상 표시
   - Vercel 프로덕션 배포 완료

4. **TikFinity 대체 기능**:
   - Sound Alerts (7가지 효과음)
   - TTS 시스템 (다국어, 속도/피치 조절)
   - Interactive Overlays (실시간 WebSocket)
   - Chatbot (스팸 필터, 자동 응답)
   - Music Player (Spotify + YouTube)
   - Analytics (실시간 차트, 수익 추적)
   - 게임 시스템 (슬롯, 룰렛, 포인트)

5. **지속적 Git 관리**:
   매 기능 완성시마다 반드시 git commit + push
   
6. **최종 목표**:
   사용자가 "와! TikFinity보다 훨씬 좋네요! 월 $200 절약됐어요!" 라고 말할 수 있는 완성품

**중요**: claude.md 파일을 꼭 읽어보시고, 모든 세부 사항을 참고해서 완벽하게 완성해주세요. 실행 가능성이 가장 중요합니다!
```

### **🎯 핵심 키워드 (AI가 놓치지 말아야 할 것들)**
- **Serena MCP 필수 사용**
- **.env UTF-8 인코딩 문제 해결**
- **FastAPI create_app 오류 수정**
- **TikTokLive 실시간 연결**
- **50+개 명령어 시스템**
- **Vercel 자동 배포**
- **Supabase 데이터베이스 연결**
- **월 $263 경제적 가치 달성**

### **📋 체크리스트 (AI가 완료해야 할 것들)**
- [ ] Serena MCP 서버 실행 및 활용
- [ ] .env 인코딩 문제 100% 해결
- [ ] `uv run python -m src.tikbot.main` 성공
- [ ] TikTok Live 실시간 연결 확인
- [ ] 웹 대시보드 http://localhost:8000 접속
- [ ] 10종 오버레이 모두 작동 확인
- [ ] 50+개 명령어 구현 및 테스트
- [ ] Spotify + YouTube 음악 통합
- [ ] AI 채팅 응답 (Serena 연동)
- [ ] 게임 시스템 (슬롯, 룰렛)
- [ ] Analytics 실시간 대시보드
- [ ] Supabase 데이터베이스 연결
- [ ] Vercel 프로덕션 배포
- [ ] 최종 사용자 테스트 성공

---

📅 **작성일:** 2025-08-07  
👤 **요청자:** TikTok Live 방송 자동화를 원하는 사용자  
🎯 **목표:** 완전히 작동하는 무료 TikBot 완성  
⚡ **우선순위:** 실행 가능성 > 기능 완성도 > 코드 품질  
🎊 **성공 조건:** 사용자가 "와! 정말 잘 되네요!" 라고 감탄할 수 있어야 함  
🚀 **Serena MCP:** 모든 문제 해결에 적극 활용 필수  
🌐 **최종 목표:** Vercel 배포 + Supabase 연결 + 프로덕션 운영

# Demo Data Generator

AI 기반 데모 로그 데이터 생성기 - ThinkingEngine 형식의 현실적인 분석 데이터를 생성합니다.

## 개요

이 프로젝트는 이벤트 택소노미(Event Taxonomy)를 기반으로 AI를 활용하여 현실적인 사용자 행동 로그 데이터를 생성합니다. 생성된 데이터는 ThinkingEngine JSON 형식으로 출력되며, 분석 및 테스트 목적으로 사용할 수 있습니다.

## 주요 기능

- 📊 **Excel/CSV 택소노미 지원**: 이벤트 데이터 수집 계획을 Excel 또는 CSV로 정의
- 🤖 **AI 기반 행동 시뮬레이션**: OpenAI 또는 Claude API를 사용한 현실적인 사용자 행동 패턴 생성
- 🎭 **다양한 시나리오**: 신규 유저, 파워 유저, 이탈 유저 등 여러 행동 시나리오 지원
- ⏰ **시간 패턴**: 시간대별, 요일별 활동 분포 반영
- 🌐 **다양한 산업 지원**: 게임, 전자상거래, 미디어, 금융 등 여러 산업 지원
- 📱 **멀티 플랫폼**: 모바일 앱, 웹, 데스크톱 지원

## 설치

### 1. 저장소 클론

```bash
git clone <repository-url>
cd demo_data_generator
```

### 2. 가상환경 생성 및 활성화

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env` 파일을 생성하고 API 키와 설정을 입력합니다:

```bash
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력
```

필수 설정:
```bash
# AI API 키 (필수)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# ThinkingEngine 설정 (업로드 기능 사용 시 필수)
TE_APP_ID=63565828675d4b9f88bbf908edf4bc1c
TE_RECEIVER_URL=https://te-receiver-naver.thinkingdata.kr/

# LogBus2 설정 (선택사항)
LOGBUS_PATH=./logbus 2/logbus
LOGBUS_CPU_LIMIT=4
```

## 사용법

### 1. 대화형 모드 (권장)

```bash
python -m data_generator.main interactive
```

단계별 안내를 따라 쉽게 데이터를 생성할 수 있습니다.

### 2. CLI 명령 모드

```bash
python -m data_generator.main generate \
  --taxonomy event_tracking/data/예시\ -\ 방치형\ 게임.xlsx \
  --product-name "My Idle Game" \
  --industry game_idle \
  --platform mobile_app \
  --start-date 2024-01-01 \
  --end-date 2024-01-07 \
  --dau 100 \
  --ai-provider anthropic
```

### 3. 데이터 업로드

생성된 데이터를 ThinkingEngine으로 업로드:

```bash
# .env에 설정이 있는 경우
python -m data_generator.main upload \
  -f ./data_generator/output/logs_YYYYMMDD_HHMMSS.jsonl

# 또는 직접 지정
python -m data_generator.main upload \
  -f ./data_generator/output/logs_YYYYMMDD_HHMMSS.jsonl \
  -a YOUR_APP_ID \
  -u https://te-receiver-naver.thinkingdata.kr/
```

자세한 업로드 가이드: [UPLOAD_GUIDE.md](UPLOAD_GUIDE.md)

### 4. 택소노미 파일 검사

```bash
python -m data_generator.main inspect event_tracking/data/예시\ -\ 방치형\ 게임.xlsx
```

### 명령어 도움말

```bash
python -m data_generator.main --help
python -m data_generator.main generate --help
python -m data_generator.main upload --help
```

## 산업 유형

- `game_idle`: 방치형 게임
- `game_rpg`: RPG 게임
- `game_puzzle`: 퍼즐 게임
- `game_casual`: 캐주얼 게임
- `ecommerce`: 전자상거래
- `media_streaming`: 미디어 스트리밍
- `social_network`: 소셜 네트워크
- `fintech`: 금융 서비스
- `education`: 교육
- `health_fitness`: 건강/피트니스
- `saas`: SaaS 제품
- `other`: 기타

## 플랫폼 유형

- `mobile_app`: 모바일 앱
- `web`: 웹
- `desktop`: 데스크톱
- `hybrid`: 하이브리드

## 시나리오 유형

- `normal`: 일반 유저 (70%)
- `new_user_onboarding`: 신규 유저 온보딩
- `power_user`: 파워 유저/고래 (10%)
- `churning_user`: 이탈 위험 유저 (20%)
- `churned_user`: 이탈 유저
- `returning_user`: 복귀 유저
- `converting_user`: 전환 유저

## 프로젝트 구조

```
demo_data_generator/
├── data_generator/           # 데이터 생성기 메인 모듈
│   ├── config/              # 설정 스키마
│   ├── models/              # 데이터 모델 (taxonomy, event, user)
│   ├── readers/             # Excel/CSV 리더
│   ├── generators/          # 생성기 (user, behavior, log)
│   ├── patterns/            # 행동 패턴 (시간, 시나리오)
│   ├── ai/                  # AI 클라이언트 (OpenAI, Claude)
│   ├── output/              # 생성된 데이터 출력
│   └── main.py              # CLI 진입점
│
├── event_tracking/          # 이벤트 트래킹 정책 생성기
│   ├── data/                # 예시 택소노미 파일
│   └── templates/           # 템플릿
│
├── requirements.txt         # Python 의존성
└── README.md               # 문서
```

## 출력 형식

생성된 로그는 ThinkingEngine JSON Lines 형식입니다:

### Track Event (행동 기록)

```json
{
  "#type": "track",
  "#account_id": "user_abc123",
  "#distinct_id": "device_xyz789",
  "#time": "2024-01-01 14:30:25.123",
  "#event_name": "stage_clear",
  "properties": {
    "channel": "organic",
    "tmp_level": 15,
    "stage_id": "stage_1_5",
    "clear_time": 120.5
  }
}
```

### User Update (상태 갱신)

```json
{
  "#type": "user_set",
  "#account_id": "user_abc123",
  "#time": "2024-01-01 14:30:25.123",
  "properties": {
    "current_level": 16,
    "total_play_time": 3600
  }
}
```

## 참고 문서

- [ThinkingEngine 데이터 구조](./ThinkingEngine.md)
- Event Taxonomy Excel 예시: `event_tracking/data/예시 - 방치형 게임.xlsx`

## 라이선스

MIT License

## 기여

이슈와 PR을 환영합니다!

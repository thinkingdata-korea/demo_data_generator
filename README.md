# AI-Powered Demo Data Generator

**빠르고, 쉽고, 글로벌한** AI 기반 데모 로그 데이터 생성기

## 개요

이 프로젝트는 기존 택소노미 기반 생성기의 한계를 극복하기 위해 개발되었습니다:

- **기존 도구의 문제**: 랜덤 값 생성, 복잡한 사용성, 중국 시장 중심
- **새로운 접근**: AI가 택소노미를 분석하여 **논리적이고 현실적인** 데이터를 **10분 안에 생성**
- **글로벌 지원**: 한국, 일본, 미국 등 모든 시장의 데이터 생성 가능

생성된 데이터는 ThinkingEngine JSONL 형식으로 출력되며, LogBus2를 통해 ThinkingEngine으로 업로드할 수 있습니다.

## 주요 기능

### 🎯 핵심 강점 (기존 도구 대비)

| 항목 | 기존 도구 | 새 시스템 |
|------|----------|-----------|
| **데이터 품질** | 랜덤 값 (논리적 오류 많음) | AI 기반 맥락 생성 (논리적 일관성) |
| **사용 편의성** | 복잡한 설정 파일 수정 | 대화형 CLI (10분 내 생성) |
| **글로벌 지원** | 중국 시장 중심 | 한국/일본/미국 모두 지원 |
| **범용성** | 산업별 별도 작업 | 모든 산업 단일 코드로 지원 |
| **비용** | N/A | AI 1회 분석 → 무한 생성 (99.97% 절감) |

**주요 개선 사항**:
- ✅ **랜덤 → AI**: LG U+ in USA 같은 오류 제로, 논리적으로 일관된 데이터
- ✅ **복잡 → 쉬움**: 복잡한 설정 대신 택소노미만 업로드하면 자동 생성
- ✅ **중국 → 글로벌**: Faker 다국어 지원 (ko_KR, en_US, ja_JP, zh_CN)
- ✅ **산업별 → 범용**: Engagement Tier로 게임/이커머스/SaaS 통일

### 🤖 AI 기반 지능형 생성

- 📊 **Excel/CSV 택소노미 지원**: 이벤트 데이터 수집 계획을 Excel 또는 CSV로 정의
- 🧠 **AI 기반 속성 생성**: 택소노미를 분석하여 **산업별 현실적인 속성값 자동 생성**
  - 속성 간 관계 자동 파악 (레벨 → XP, 공격력 → 전투력 등)
  - 산업별 적절한 값 범위 자동 결정
  - 현실적인 아이템/제품명 생성 (AI가 20-50개 예시 제공)
  - **Faker 폴백**: 40+ 속성 패턴 자동 인식 (name, email, phone, address 등)
- 🤖 **AI 기반 행동 시뮬레이션**: OpenAI 또는 Claude API를 사용한 현실적인 사용자 행동 패턴 생성
- ⚡ **속성 업데이트 엔진**: 이벤트 발생 시 유저 속성 자동 업데이트 (AI가 규칙 생성)
  - 게임: `stage_clear` → level +1, gold +100
  - 이커머스: `purchase` → total_purchases +1, total_spent += amount
  - SaaS: `feature_used` → usage_count +1

### 🎭 유저 시나리오 & 행동 패턴

- 🎭 **다양한 시나리오**: 신규 유저, 파워 유저, 이탈 유저 등 여러 행동 시나리오 지원
- 🎯 **커스텀 시나리오**: AI를 통해 자유롭게 정의한 사용자 행동 패턴 생성 가능
- ⏰ **시간 패턴**: 시간대별, 요일별 활동 분포 반영
- 🔄 **유저 라이프사이클**: 7단계 생명주기 관리 (INSTALLED → ACTIVE → ADVANCED)

### 🌐 산업 & 플랫폼 지원

- 🌐 **완전 범용 산업 지원**: 게임, 전자상거래, 미디어, 금융, SaaS 등 (커스텀 산업도 즉시 지원!)
- 📱 **멀티 플랫폼**: 모바일 앱, 웹, 데스크톱 지원
- 🔧 **프리셋 속성 자동 생성**: 플랫폼별 필수 프리셋 속성 자동 포함 (OS, 디바이스, 브라우저 정보 등)

### 💾 데이터 관리 & 업로드

- 📂 **일일 분할 파일 생성**: 대용량 데이터를 날짜별로 분할하여 메모리 효율적 생성
- 📤 **LogBus2 연동**: 생성된 데이터를 ThinkingEngine으로 자동 업로드 (단일/다중 파일 지원)
- 💾 **설정 관리**: API 키, APP ID 등 자동 저장으로 반복 입력 불필요
- 💰 **비용 최적화**: AI 분석 캐싱으로 반복 실행 시 비용 제로

## 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone <repository-url>
cd demo_data_generator

# 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 설정 관리

프로그램을 처음 실행하면 필요한 설정들(API 키, ThinkingEngine APP ID 등)을 입력받습니다.
입력된 설정은 자동으로 저장되어 다음 실행부터는 재입력이 필요하지 않습니다.

#### 설정 관리 명령어

```bash
# 저장된 설정 확인
python -m data_generator.main settings

# 저장된 설정 삭제 (초기화)
python -m data_generator.main clear-settings
```

#### 환경 변수 설정 (선택사항)

설정을 프로젝트 루트에 `.env` 파일로 관리할 수도 있습니다:

```bash
# AI API 키 (필수 - 하나 이상 설정)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# ThinkingEngine 설정 (업로드 기능 사용 시 필수)
TE_APP_ID=your_app_id
TE_RECEIVER_URL=https://te-receiver-naver.thinkingdata.kr/

# LogBus2 설정 (선택사항)
LOGBUS_PATH=./logbus 2/logbus
LOGBUS_CPU_LIMIT=4
```

> **참고**: 대화형 모드에서 입력한 설정은 `~/.demo_data_generator_config.json`에 저장됩니다.

### 3. 대화형 모드로 시작 (권장)

```bash
python -m data_generator.main interactive
```

단계별 안내를 따라 쉽게 데이터를 생성할 수 있습니다.

## 사용법

### 1. 대화형 모드

가장 쉽고 권장되는 방법입니다:

```bash
python -m data_generator.main interactive
```

### 2. CLI 명령 모드

명령줄 인터페이스를 통한 데이터 생성:

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

#### 주요 옵션

- `--taxonomy`, `-t`: 택소노미 파일 경로 (Excel/CSV) **(필수)**
- `--product-name`, `-p`: 제품/앱 이름 **(필수)**
- `--industry`, `-i`: 산업 유형 **(필수)**
- `--platform`: 플랫폼 유형 **(필수)**
- `--start-date`: 시작 날짜 (YYYY-MM-DD) **(필수)**
- `--end-date`: 종료 날짜 (YYYY-MM-DD) **(필수)**
- `--dau`: 일일 활성 사용자 수 **(필수)**
- `--ai-provider`: AI 제공자 (openai/anthropic, 기본값: openai)
- `--ai-model`: AI 모델 이름 (선택)
- `--description`: 앱/제품 특성 설명
- `--avg-events-min`: 1인당 하루 평균 최소 이벤트 수 (기본값: 5)
- `--avg-events-max`: 1인당 하루 평균 최대 이벤트 수 (기본값: 30)
- `--output-dir`, `-o`: 출력 디렉토리 (기본값: ./data_generator/output)

### 3. 택소노미 파일 검사

택소노미 파일의 구조와 내용을 확인:

```bash
python -m data_generator.main inspect event_tracking/data/예시\ -\ 방치형\ 게임.xlsx
```

### 4. 데이터 업로드

생성된 데이터를 ThinkingEngine으로 업로드:

```bash
# 단일 파일 업로드
python -m data_generator.main upload \
  -f ./data_generator/output/logs_20240101.jsonl

# 디렉토리 내 모든 파일 업로드 (일일 분할 파일)
python -m data_generator.main upload \
  -d ./data_generator/output

# 설정이 저장되어 있으면 APP_ID 등을 자동으로 사용
# 처음 실행 시 대화형으로 설정 입력 후 자동 저장됨
```

#### 업로드 옵션

- `--data-file`, `-f`: 단일 파일 업로드 경로
- `--data-dir`, `-d`: 디렉토리 업로드 경로 (일일 분할 파일용)
- `--app-id`, `-a`: ThinkingEngine APP ID (저장된 설정 사용 가능)
- `--push-url`, `-u`: ThinkingEngine Receiver URL (저장된 설정 사용 가능)
- `--logbus-path`, `-l`: LogBus2 바이너리 경로 (저장된 설정 사용 가능)
- `--cpu-limit`: CPU 코어 수 제한
- `--compress`: Gzip 압축 사용 (기본값: true)
- `--auto-remove`: 업로드 후 파일 자동 삭제
- `--remove-after-days`: 파일 삭제 기간 (일, 기본값: 7)

> **팁**: 설정은 `~/.demo_data_generator_config.json`에 저장되므로 매번 입력할 필요가 없습니다!

자세한 업로드 가이드: [UPLOAD_GUIDE.md](./UPLOAD_GUIDE.md)

### 5. 명령어 도움말

```bash
python -m data_generator.main --help
python -m data_generator.main generate --help
python -m data_generator.main upload --help
```

## 설정 옵션

### 산업 유형 (Industry Type)

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

### 플랫폼 유형 (Platform Type)

- `mobile_app`: 모바일 앱
- `web`: 웹
- `desktop`: 데스크톱
- `hybrid`: 하이브리드

### 시나리오 유형 (Scenario Type)

시스템이 자동으로 다양한 유저 시나리오를 생성합니다:

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
├── data_generator/           # 메인 모듈
│   ├── config/              # 설정 스키마
│   ├── models/              # 데이터 모델 (taxonomy, event, user)
│   ├── readers/             # Excel/CSV 리더
│   ├── generators/          # 생성기 (user, behavior, log)
│   ├── patterns/            # 행동 패턴 (시간, 시나리오)
│   ├── ai/                  # AI 클라이언트 (OpenAI, Claude)
│   ├── uploader/            # LogBus2 업로더
│   ├── output/              # 생성된 데이터 출력 디렉토리
│   ├── interactive.py       # 대화형 모드
│   └── main.py              # CLI 진입점
│
├── event_tracking/          # 이벤트 트래킹 정책
│   └── data/                # 예시 택소노미 파일
│
├── docs/                    # 문서
│   ├── README.md            # 메인 문서 (이 파일)
│   ├── ThinkingEngine.md    # ThinkingEngine 데이터 형식
│   ├── UPLOAD_GUIDE.md      # 업로드 가이드
│   └── logbus2.md           # LogBus2 설정 가이드
│
├── logbus 2/                # LogBus2 설정 및 바이너리
│   └── conf/                # LogBus2 설정 파일
│
├── requirements.txt         # Python 의존성
├── .env                     # 환경 변수 (git에서 제외)
└── .gitignore
```

## 출력 형식

생성된 로그는 ThinkingEngine JSON Lines (.jsonl) 형식입니다.

### Track Event (행동 기록)

모든 이벤트에는 **플랫폼별 프리셋 속성이 자동으로 포함**됩니다.

```json
{
  "#type": "track",
  "#account_id": "user_abc123",
  "#distinct_id": "device_xyz789",
  "#time": "2024-01-01 14:30:25.123",
  "#event_name": "stage_clear",
  "properties": {
    // 프리셋 속성 (플랫폼별 자동 생성)
    "#ip": "123.45.67.89",
    "#country": "South Korea",
    "#country_code": "KR",
    "#os": "Android",
    "#os_version": "13",
    "#device_model": "Galaxy S23",
    "#app_version": "1.2.0",
    "#network_type": "WIFI",

    // 공통 속성 (택소노미 정의)
    "channel": "organic",
    "tmp_level": 15,

    // 이벤트 속성
    "stage_id": "stage_1_5",
    "clear_time": 120.5
  }
}
```

### 프리셋 속성 자동 생성

플랫폼에 따라 다음과 같은 프리셋 속성이 자동으로 포함됩니다:

#### 모든 플랫폼 공통
- `#ip`, `#country`, `#country_code`, `#province`, `#city`
- `#lib`, `#lib_version`, `#zone_offset`
- `#device_id`, `#screen_width`, `#screen_height`
- `#system_language`

#### 모바일 앱 전용
- `#os`, `#os_version`, `#manufacturer`, `#device_model`, `#device_type`
- `#app_version`, `#bundle_id`, `#network_type`, `#carrier`
- `#install_time`, `#simulator`, `#ram`, `#disk`, `#fps`

#### 웹 전용
- `#os`, `#os_version`
- `#browser`, `#browser_version`, `#ua`, `#utm`

#### 데스크톱 전용
- `#os`, `#os_version`, `#device_model`

> **참고**: 프리셋 속성에 대한 상세 설명은 [docs/Preset Properties.md](./Preset%20Properties.md)를 참조하세요.

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

## LogBus2 설치

데이터를 ThinkingEngine으로 업로드하려면 LogBus2 바이너리가 필요합니다:

1. [ThinkingData LogBus2](https://docs.thinkingdata.cn/ta-manual/latest/installation/installation_menu/client_sdk/logbus_v2.html) 다운로드
2. `logbus 2/logbus` 경로에 바이너리 파일 배치
3. `.env` 파일에서 `LOGBUS_PATH` 설정

자세한 설정은 [UPLOAD_GUIDE.md](./UPLOAD_GUIDE.md)를 참조하세요.

## 참고 문서

- [ThinkingEngine 데이터 구조](./ThinkingEngine.md)
- [업로드 가이드](./UPLOAD_GUIDE.md)
- [LogBus2 설정 가이드](./logbus2.md)
- 택소노미 예시: `event_tracking/data/예시 - 방치형 게임.xlsx`

## 예시 워크플로우

```bash
# 1. 대화형 모드로 데이터 생성 (권장)
python -m data_generator.main interactive

# 2. 생성된 파일 확인
ls -lh data_generator/output/
# 출력 예시:
# logs_20240101.jsonl  859MB
# logs_20240102.jsonl  852MB
# logs_20240103.jsonl  878MB
# ...

# 3. ThinkingEngine으로 업로드 (디렉토리 전체)
python -m data_generator.main upload -d data_generator/output

# 또는 특정 파일만 업로드
python -m data_generator.main upload -f data_generator/output/logs_20240101.jsonl
```

## AI 기반 데이터 품질

이 생성기는 단순한 랜덤 데이터가 아닌, **AI가 택소노미를 분석**하여 **산업 무관하게 현실적인 데이터**를 생성합니다:

### 🧠 지능형 속성 생성 (완전 범용)

```
1. 택소노미 분석 (1회만!)
   ↓
2. AI가 속성 간 관계 파악 (산업 무관)
   - 게임: level → XP, attack → combat_power
   - 이커머스: order_count → total_spent
   - SaaS: usage_count → subscription_level
   ↓
3. Engagement Tier 기반 값 분포 ⭐ 핵심!
   - NEW_USER (very_low): 최소값 근처 (10%)
   - ACTIVE_USER (medium): 중간값 (50%)
   - POWER_USER (very_high): 최대값 근처 (90%)
   → 게임/이커머스/SaaS 모두 동일한 로직!
   ↓
4. AI + Faker 하이브리드 생성
   - AI 분석: 속성 의미 파악, 범위 결정, 예시값 제공
   - Faker 폴백: 40+ 패턴 (name, email, phone, address, company 등)
   - 다국어 지원: country 기반 locale 자동 선택
   ↓
5. 현실적인 값 생성 (산업별)
   - 게임: "Flame Sword", "Dragon Armor", level=85
   - 이커머스: "iPhone 15 Pro", "Galaxy S24", total_spent=350000
   - SaaS: "Premium Plan", usage_count=1240
   - 채널: "organic", "google_ads", "facebook_ads"
```

**결과**: 분석에 의미 있고, 어떤 산업이든 바로 사용 가능한 데이터!

### 🎯 행동 패턴 시뮬레이션

- **생명주기 기반 이벤트 필터링**:
  - INSTALLED → 앱 시작만 가능
  - FIRST_SESSION → 튜토리얼 이벤트만
  - ACTIVE → 일반 이벤트
  - ADVANCED → 고급 기능 이벤트
- **이벤트 시퀀스**: 앱 시작 → 튜토리얼 → 레벨업 → 구매 (자연스러운 흐름)
- **시간 패턴**: 출퇴근 시간에 많고, 새벽에 적음
- **유저 세그먼트**: 신규/파워/이탈 유저별 다른 행동 패턴
- **속성 자동 업데이트**: 이벤트 발생 시 유저 상태 자동 변경 (AI가 규칙 생성)

## 문제 해결

### API 키 오류
- `.env` 파일에 올바른 API 키가 설정되어 있는지 확인하세요.
- OpenAI 또는 Anthropic 중 하나 이상의 API 키가 필요합니다.

### LogBus2 업로드 실패
- LogBus2 바이너리 파일이 올바른 경로에 있는지 확인하세요.
- `.env` 파일의 `TE_APP_ID`와 `TE_RECEIVER_URL`이 올바른지 확인하세요.
- [UPLOAD_GUIDE.md](./UPLOAD_GUIDE.md)를 참조하세요.

### 택소노미 파일 오류
- Excel/CSV 파일이 올바른 형식인지 확인하세요.
- `inspect` 명령어로 파일 구조를 검증할 수 있습니다.

## 라이선스

MIT License

## 기여

이슈와 PR을 환영합니다!

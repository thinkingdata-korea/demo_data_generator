# Demo Data Generator - 시스템 아키텍처

## 개요

Demo Data Generator는 **AI 기반 택소노미 분석**을 통해 **현실적이고 논리적으로 일관된 제품 분석 데이터**를 생성하는 시스템입니다.

### 핵심 설계 철학

1. **AI-First**: 하드코딩 제거, AI가 택소노미를 분석하여 규칙 자동 생성
2. **Industry-Agnostic**: 게임/이커머스/SaaS 등 모든 산업을 단일 코드로 지원
3. **Taxonomy-Driven**: 택소노미 정의가 곧 데이터 생성 규칙
4. **Lifecycle-Aware**: 유저 생명주기 단계에 따른 현실적인 행동 패턴
5. **Cost-Optimized**: AI 분석 1회 → 캐싱 → 무한 재사용

---

## 시스템 아키텍처

### 전체 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Generation Orchestrator                  │
│                  (core/orchestrator.py)                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    ▼                       ▼                       ▼
┌─────────┐         ┌──────────────┐       ┌──────────────┐
│Taxonomy │         │  AI Client   │       │Cache Manager │
│ Reader  │         │(OpenAI/Claude)       │              │
└─────────┘         └──────────────┘       └──────────────┘
    │                       │                       │
    │                       │                       │
    ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│         IntelligentPropertyGenerator (단 1회 AI 분석)            │
│  - 속성 관계 분석                                                 │
│  - 이벤트 구조 분석 (시퀀스, 퍼널, 전제조건)                      │
│  - 세그먼트별 행동 패턴 분석                                      │
│  - 결과: property_rules (모든 생성기가 공유)                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│     User     │    │   Behavior   │    │     Log      │
│  Generator   │    │    Engine    │    │  Generator   │
│              │    │              │    │              │
│ AI 분석 활용 │───▶│ AI 분석 활용 │───▶│ AI 분석 활용 │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ JSONL Output │
                    │ (ThinkingData)│
                    └──────────────┘
```

---

## 핵심 컴포넌트

### 1. Taxonomy Reader (readers/taxonomy_reader.py)

Excel/CSV 파일에서 이벤트 택소노미를 로드하는 컴포넌트입니다.

#### 입력 형식

**이벤트 시트**:
| event_name | event_tag | description | properties |
|------------|-----------|-------------|------------|
| app_start | 시스템 | 앱 시작 | |
| tutorial_step1 | 튜토리얼 | 튜토리얼 1단계 | stage_id, clear_time |

**속성 시트**:
| name | type | description | constraint |
|------|------|-------------|------------|
| level | number | 유저 레벨 | 1-150 |
| country | string | 국가 | KR,JP,US |

#### 출력

```python
EventTaxonomy(
    events=[Event(...)],
    common_properties=[Property(...)],
    user_properties=[Property(...)]
)
```

---

### 2. AI Client (ai/claude_client.py, ai/openai_client.py)

AI API를 호출하여 택소노미를 분석하는 클라이언트입니다.

#### 주요 특징

- **JSON Retry Logic**: 파싱 실패 시 최대 3회 재시도
- **Rate Limiting**: API 제한 준수 (utils/rate_limiter.py)
- **Industry-Neutral Prompts**: 하드코딩된 예시 없이 플레이스홀더 기반

#### 핵심 프롬프트 구조

```
입력:
- 이벤트 목록 (event_names)
- 속성 목록 (properties)
- 제품 정보 (industry, platform, product_name, description)

분석 태스크:
1. Event Structure Analysis
   - Sequential Events (tutorial_step1 → tutorial_step2)
   - Funnels (view_product → add_to_cart → purchase)
   - Prerequisites (pvp_match requires tutorial_complete)
   - Lifecycle Progression (onboarding flow)

2. Property Relationship Analysis
   - Constraints (carrier ↔ country)
   - Dependencies (level → XP, attack → combat_power)
   - Value Ranges (min, max, mean)

3. Segment Analysis ⭐ 핵심!
   - NEW_USER, ACTIVE_USER, POWER_USER, etc.
   - property_ranges (세그먼트별 속성 범위)
   - event_sequence (전형적인 이벤트 흐름)
   - event_probabilities (이벤트 발생 확률)

출력:
{
  "property_constraints": {...},
  "event_constraints": {...},
  "property_relationships": {...},
  "value_ranges": {...},
  "segment_analysis": {...}  ⭐
}
```

---

### 3. IntelligentPropertyGenerator (generators/intelligent_property_generator.py)

**전체 시스템의 두뇌**입니다. 단 1회 AI 분석을 수행하고, 결과를 모든 생성기와 공유합니다.

#### 생명주기

```
1. 초기화 (orchestrator에서 생성)
   ↓
2. analyze_properties() 호출 (단 1회!)
   - AI에게 택소노미 전달
   - 속성/이벤트 관계 분석
   - 세그먼트별 행동 패턴 분석
   - 결과를 self.property_rules에 저장
   ↓
3. 모든 생성기에게 전달
   - UserGenerator
   - BehaviorEngine
   - LogGenerator
   ↓
4. 속성 생성 시 규칙 적용
   - generate_property_value() 호출
   - AI 분석 결과 기반 생성 (AI 재호출 없음!)
```

#### AI 분석 결과 구조 (property_rules)

```json
{
  "property_constraints": {
    "carrier": {
      "depends_on": ["country"],
      "mapping": {
        "KR": ["SKT", "KT", "LG U+"],
        "US": ["Verizon", "AT&T", "T-Mobile"],
        "JP": ["NTT Docomo", "au", "SoftBank"]
      }
    }
  },

  "property_relationships": {
    "level": {
      "type": "number",
      "depends_on": [],
      "affects": ["xp", "combat_power"]
    },
    "xp": {
      "type": "number",
      "depends_on": ["level"],
      "formula": "level * 100 + random(0-50)"
    }
  },

  "value_ranges": {
    "level": {"min": 1, "max": 150, "mean": 50},
    "gold": {"min": 0, "max": 1000000, "mean": 50000}
  },

  "segment_analysis": {
    "NEW_USER": {
      "property_ranges": {
        "level": {"min": 1, "max": 5, "mean": 2},
        "gold": {"min": 0, "max": 500, "mean": 200},
        "playtime_minutes": {"min": 5, "max": 30, "mean": 15}
      },
      "event_sequence": [
        "app_install",
        "app_start",
        "tutorial_step1",
        "tutorial_step2",
        "tutorial_completed",
        "first_stage_start"
      ],
      "event_probabilities": {
        "tutorial_step1": 0.95,
        "tutorial_completed": 0.70,
        "first_purchase": 0.02
      }
    },

    "POWER_USER": {
      "property_ranges": {
        "level": {"min": 100, "max": 150, "mean": 130},
        "gold": {"min": 80000, "max": 500000, "mean": 200000},
        "playtime_minutes": {"min": 60, "max": 240, "mean": 120}
      },
      "event_sequence": [
        "app_start",
        "daily_reward_claim",
        "pvp_match",
        "raid_start",
        "guild_activity",
        "purchase",
        "app_end"
      ],
      "event_probabilities": {
        "pvp_match": 0.90,
        "purchase": 0.20,
        "raid_start": 0.85
      }
    }
  }
}
```

#### 속성 생성 로직

```python
def generate_property_value(
    self,
    prop_name: str,
    prop_type: str,
    user: Optional[User],
    event_name: Optional[str] = None
) -> Any:
    """
    AI 분석 결과를 활용하여 속성값 생성 (AI 재호출 없음!)

    1. Constraint 체크 (carrier ↔ country)
    2. Dependency 체크 (level → xp)
    3. Segment-aware 범위 적용 (NEW_USER: level 1-5)
    4. Faker 폴백 (name, email, phone 등 40+ 패턴)
    """
    # 1. property_constraints 확인
    if prop_name in self.property_rules.get("property_constraints", {}):
        # 의존 속성 값에 따라 생성
        pass

    # 2. property_relationships 확인
    if prop_name in self.property_rules.get("property_relationships", {}):
        # 관계식에 따라 계산
        pass

    # 3. segment_analysis에서 범위 가져오기
    if user and user.segment:
        segment_key = user.segment.value.upper()
        segment_ranges = self.property_rules["segment_analysis"][segment_key]["property_ranges"]
        if prop_name in segment_ranges:
            # 세그먼트별 범위 내에서 생성
            pass

    # 4. Faker 폴백
    return self._fallback_faker_generation(prop_name, prop_type)
```

---

### 4. User Generator (generators/user_generator.py)

가상 유저를 생성하는 컴포넌트입니다.

#### 유저 세그먼트

```python
class UserSegment(Enum):
    NEW_USER = "new_user"           # 신규 유저 (0-3일)
    ACTIVE_USER = "active_user"     # 일반 활성 유저
    POWER_USER = "power_user"       # 파워 유저 (고래)
    CHURNING_USER = "churning_user" # 이탈 위험 유저
    CHURNED_USER = "churned_user"   # 이탈 유저
    RETURNING_USER = "returning_user" # 복귀 유저
```

#### 생명주기 단계

```python
class LifecycleStage(Enum):
    INSTALLED = "installed"                 # 앱 설치만 함
    FIRST_SESSION = "first_session"         # 첫 세션 진행 중
    REGISTERED = "registered"               # 회원가입 완료
    ONBOARDING_STARTED = "onboarding_started"   # 온보딩 시작
    ONBOARDING_COMPLETED = "onboarding_completed" # 온보딩 완료
    ACTIVE = "active"                       # 일반 활성 상태
    ADVANCED = "advanced"                   # 고급 기능 사용
```

#### AI 분석 결과 활용

**Before (하드코딩)**:
```python
characteristics = {
    UserSegment.NEW_USER: {
        "daily_session_count": random.randint(2, 5),
        "session_duration_minutes": random.uniform(10, 25),
        "conversion_probability": 0.02,
    }
}
```

**After (AI 분석 활용)**:
```python
def _get_segment_characteristics(self, segment: UserSegment):
    # AI 분석 결과에서 세그먼트별 특성 가져오기
    segment_analysis = self.intelligent_generator.property_rules.get("segment_analysis", {})
    segment_key = segment.value.upper()

    if segment_key in segment_analysis:
        ai_data = segment_analysis[segment_key]

        # property_ranges에서 실제 범위 추출
        property_ranges = ai_data.get("property_ranges", {})

        # event_probabilities에서 전환 확률 추정
        event_probs = ai_data.get("event_probabilities", {})
        conversion_prob = max([
            prob for event, prob in event_probs.items()
            if "purchase" in event.lower() or "subscribe" in event.lower()
        ], default=0.02)

        return {
            "conversion_probability": conversion_prob,
            # ... 기타 특성
        }
```

#### 유저 생성 흐름

```
1. 세그먼트 결정 (비율: NEW 30%, ACTIVE 40%, POWER 10%, etc.)
   ↓
2. 생명주기 단계 결정 (세그먼트 + 가입일에 따라)
   - NEW_USER: INSTALLED → FIRST_SESSION → ONBOARDING_STARTED
   - ACTIVE_USER: ACTIVE
   - POWER_USER: ADVANCED
   ↓
3. 가입일 결정
   - NEW_USER: 생성 기간 내 0-3일 전
   - ACTIVE_USER: 7-30일 전
   - RETURNING_USER: 60-90일 전, 최근 복귀
   ↓
4. 유저 속성 생성 (IntelligentPropertyGenerator 활용)
   - 세그먼트별 property_ranges 적용
   - level, gold, playtime 등 자동 생성
```

---

### 5. Behavior Engine (generators/behavior_engine.py)

유저 행동 패턴을 생성하는 컴포넌트입니다.

#### 주요 기능

##### 1) 세션 생성 (generate_daily_sessions)

```python
def generate_daily_sessions(
    self,
    user: User,
    date: datetime,
    behavior_pattern: Dict[str, Any]
) -> List[tuple]:
    """
    특정 날짜에 유저가 활동할 세션 시간대 생성

    Returns:
        [(start_time, end_time), ...]
    """
    # 1. 활동 확률 체크 (세그먼트별 다름)
    if not TimePatternGenerator.should_user_be_active(
        date=date,
        user_segment=user.segment.value,
        base_daily_probability=behavior_pattern.get("activity_probability", 0.7)
    ):
        return []

    # 2. 세션 횟수 결정 (1-5회)
    session_range = behavior_pattern.get("daily_session_range", (1, 3))
    session_count = random.randint(session_range[0], session_range[1])

    # 3. 시간대 분포 (출퇴근 시간 많음, 새벽 적음)
    time_pattern_type = behavior_pattern.get("time_pattern", "normal")
    hourly_dist = TimePatternGenerator.get_hourly_distribution(time_pattern_type)

    # 4. 세션 시간대 생성
    sessions = TimePatternGenerator.generate_session_times(
        date=date,
        session_count=session_count,
        hourly_dist=hourly_dist,
        session_duration_minutes=avg_duration
    )

    return sessions
```

##### 2) 이벤트 선택 (select_events_for_session)

**AI 분석의 event_sequence를 100% 따름!**

```python
def select_events_for_session(
    self,
    user: User,
    session_duration_minutes: float,
    behavior_pattern: Dict[str, Any]
) -> List[str]:
    """
    세션 내에서 발생할 이벤트 선택

    우선순위:
    1. AI event_sequence (있으면 100% 따름)
    2. 폴백: event_probabilities 기반 랜덤 선택
    """

    # 1. AI 분석 결과에서 이벤트 시퀀스 가져오기
    ai_event_sequence = self._get_ai_event_sequence(user.segment)

    if ai_event_sequence:
        # 시퀀스 따르기 (순서 보장!)
        sequence_events = self._select_from_sequence(
            ai_event_sequence,
            session_duration_minutes,
            user
        )
        if sequence_events:
            return sequence_events

    # 2. 폴백: event_probabilities 기반
    ai_event_probs = self._get_ai_event_probabilities(user.segment)

    # 3. 생명주기 필터링 (중요!)
    available_events = []
    for event in self.taxonomy.events:
        if self.lifecycle_rules.is_event_allowed_in_lifecycle(
            event.event_name,
            user.lifecycle_stage
        ):
            available_events.append(event)

    # 4. 확률 기반 선택
    weights = [ai_event_probs.get(e.event_name, 1.0) for e in available_events]
    selected = random.choices(available_events, weights=weights, k=event_count)

    return [e.event_name for e in selected]
```

#### 생명주기 규칙 (patterns/lifecycle_rules.py)

```python
class LifecycleRulesEngine:
    """
    유저 생명주기 단계별 허용 이벤트 제약
    """

    LIFECYCLE_EVENT_RULES = {
        LifecycleStage.INSTALLED: [
            "app_install", "app_start", "signup"
        ],
        LifecycleStage.FIRST_SESSION: [
            "app_start", "signup", "tutorial_*", "onboarding_*"
        ],
        LifecycleStage.ONBOARDING_STARTED: [
            "app_start", "tutorial_*", "onboarding_*", "first_*"
        ],
        LifecycleStage.ONBOARDING_COMPLETED: [
            "app_start", "*_start", "*_end", "basic_*"
        ],
        LifecycleStage.ACTIVE: [
            "*"  # 대부분 이벤트 허용
        ],
        LifecycleStage.ADVANCED: [
            "*"  # 모든 이벤트 허용
        ]
    }
```

---

### 6. Log Generator (generators/log_generator.py)

최종 이벤트 로그를 생성하는 컴포넌트입니다.

#### 로그 생성 흐름

```
1. 각 유저별로 날짜 순회
   ↓
2. BehaviorEngine에서 세션 시간 가져오기
   ↓
3. 각 세션별로 이벤트 선택
   ↓
4. 각 이벤트별로 속성 생성
   ├─ IntelligentPropertyGenerator 활용
   ├─ 세그먼트별 제약 자동 적용
   ├─ 속성 간 관계 자동 반영
   └─ PresetPropertiesGenerator로 플랫폼 속성 추가
   ↓
5. ThinkingData 형식으로 변환
   ├─ Track Event: {"#type": "track", ...}
   └─ User Update: {"#type": "user_set", ...}
   ↓
6. JSONL 파일로 저장 (날짜별 분할)
```

#### 속성 업데이트 엔진 (generators/property_update_engine.py)

이벤트 발생 시 유저 속성을 자동으로 업데이트합니다.

```python
class PropertyUpdateEngine:
    """
    이벤트 발생 시 유저 속성 자동 업데이트

    예시:
    - stage_clear → level += 1, gold += 100
    - purchase → total_purchases += 1, total_spent += amount
    - feature_used → usage_count += 1
    """

    def __init__(self, ai_client: BaseAIClient, taxonomy: EventTaxonomy):
        self.ai_client = ai_client
        self.taxonomy = taxonomy
        self.update_patterns = {}  # 캐시

    def update_user_properties(
        self,
        user: User,
        event_name: str,
        event_properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        이벤트에 따라 유저 속성 업데이트

        AI가 분석한 규칙 적용:
        - stage_clear: level +1, xp +50
        - purchase: gold -price, total_spent +price
        """
        # AI 분석 결과에서 업데이트 패턴 가져오기
        pattern = self._get_update_pattern_for_event(event_name)

        updates = {}
        for prop, update_rule in pattern.items():
            if update_rule["type"] == "increment":
                current = user.get_state(prop) or 0
                updates[prop] = current + update_rule["value"]
            elif update_rule["type"] == "decrement":
                current = user.get_state(prop) or 0
                updates[prop] = max(0, current - update_rule["value"])
            # ... 기타 업데이트 로직

        # 유저 상태 반영
        user.update_state(updates)

        return updates
```

---

### 7. Cache Manager (utils/cache_manager.py)

AI 분석 결과를 디스크에 캐싱하여 API 비용과 시간을 절약합니다.

#### 캐싱 전략

```python
def get_cache_key(
    taxonomy: EventTaxonomy,
    ai_provider: str,
    product_info: Dict[str, Any]
) -> str:
    """
    캐시 키 생성

    조합:
    - taxonomy_hash (이벤트/속성 내용의 해시)
    - ai_provider (openai/anthropic)
    - industry + platform + product_name

    변경 시 캐시 무효화:
    - 택소노미 수정
    - AI 제공자 변경
    - 제품 정보 변경
    """
    taxonomy_content = json.dumps({
        "events": [e.dict() for e in taxonomy.events],
        "properties": [p.dict() for p in taxonomy.common_properties]
    }, sort_keys=True)

    taxonomy_hash = hashlib.sha256(taxonomy_content.encode()).hexdigest()[:16]

    product_key = f"{product_info['industry']}_{product_info['platform']}_{product_info['product_name']}"

    return f"{taxonomy_hash}_{ai_provider}_{product_key}"
```

#### 캐시 효과

| 상황 | AI 호출 | 소요 시간 | 비용 |
|------|---------|----------|------|
| 첫 실행 (캐시 미스) | 1회 | ~10-30초 | ~$0.10 |
| 이후 실행 (캐시 히트) | 0회 | ~0.1초 | $0 |
| 1만 개 이벤트 생성 | 0회 | ~2초 | $0 |

**비용 절감**: 99.97% (1회 분석으로 무한 생성)

---

## 데이터 생성 플로우

### 전체 실행 흐름

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 초기화 단계 (orchestrator.execute())                       │
└─────────────────────────────────────────────────────────────┘
    │
    ├─ 0. 캐시 초기화 (매 실행마다)
    │   └─ cache_manager.clear()
    │
    ├─ 1. 택소노미 로드
    │   └─ TaxonomyReader.read() → EventTaxonomy
    │
    ├─ 2. AI 클라이언트 초기화
    │   └─ OpenAIClient or ClaudeClient
    │
    ├─ 3. IntelligentPropertyGenerator 생성
    │   ├─ 택소노미 속성 전달
    │   ├─ 제품 정보 전달 (industry, platform, product_name)
    │   └─ 이벤트 이름 전달
    │
    ├─ 4. AI 분석 수행 (단 1회!)
    │   ├─ intelligent_generator.analyze_properties()
    │   ├─ AI API 호출 (또는 캐시 로드)
    │   └─ property_rules 저장
    │       ├─ property_constraints
    │       ├─ event_constraints
    │       ├─ property_relationships
    │       ├─ value_ranges
    │       └─ segment_analysis ⭐
    │
    └─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 2. 유저 생성 단계 (user_generator.generate_users())          │
└─────────────────────────────────────────────────────────────┘
    │
    ├─ 각 세그먼트별 유저 수 결정
    │   ├─ NEW_USER: 30%
    │   ├─ ACTIVE_USER: 40%
    │   ├─ POWER_USER: 10%
    │   ├─ CHURNING_USER: 15%
    │   └─ RETURNING_USER: 5%
    │
    ├─ 각 유저별로:
    │   ├─ 세그먼트 할당
    │   ├─ 생명주기 단계 결정
    │   ├─ 가입일 결정
    │   └─ 속성 생성 (AI 분석의 segment_analysis 활용)
    │       ├─ NEW_USER: level 1-5, gold 0-500
    │       ├─ ACTIVE_USER: level 20-60, gold 5000-50000
    │       └─ POWER_USER: level 100-150, gold 80000-500000
    │
    └─ User 객체 리스트 반환

┌─────────────────────────────────────────────────────────────┐
│ 3. 행동 엔진 초기화 (behavior_engine)                         │
└─────────────────────────────────────────────────────────────┘
    │
    ├─ IntelligentPropertyGenerator 공유
    │   └─ segment_analysis 접근 가능
    │
    └─ LifecycleRulesEngine 초기화
        └─ 생명주기별 이벤트 제약 규칙

┌─────────────────────────────────────────────────────────────┐
│ 4. 로그 생성 단계 (log_generator.generate())                 │
└─────────────────────────────────────────────────────────────┘
    │
    ├─ 날짜별 순회 (start_date ~ end_date)
    │   │
    │   ├─ 유저별 순회
    │   │   │
    │   │   ├─ 유저가 이탈했는지 체크 (churned)
    │   │   │
    │   │   ├─ BehaviorEngine.generate_daily_sessions()
    │   │   │   └─ 오늘 활동할 세션 시간 생성
    │   │   │       ├─ 활동 확률 체크
    │   │   │       ├─ 세션 횟수 결정
    │   │   │       └─ 시간대 분포 적용
    │   │   │
    │   │   └─ 각 세션별로:
    │   │       │
    │   │       ├─ BehaviorEngine.select_events_for_session()
    │   │       │   ├─ AI event_sequence 우선 (있으면 100% 따름)
    │   │       │   ├─ 생명주기 필터링 (허용된 이벤트만)
    │   │       │   └─ event_probabilities 기반 선택
    │   │       │
    │   │       ├─ 각 이벤트별로:
    │   │       │   │
    │   │       │   ├─ IntelligentPropertyGenerator로 속성 생성
    │   │       │   │   ├─ segment_analysis의 property_ranges 적용
    │   │       │   │   ├─ property_constraints 적용 (carrier ↔ country)
    │   │       │   │   ├─ property_relationships 적용 (level → xp)
    │   │       │   │   └─ Faker 폴백 (name, email, phone 등)
    │   │       │   │
    │   │       │   ├─ PresetPropertiesGenerator로 플랫폼 속성 추가
    │   │       │   │   ├─ #os, #device_model, #app_version
    │   │       │   │   └─ #country, #ip, #network_type
    │   │       │   │
    │   │       │   ├─ Track Event 생성
    │   │       │   │   {"#type": "track", "#event_name": "...", ...}
    │   │       │   │
    │   │       │   └─ PropertyUpdateEngine로 유저 속성 업데이트
    │   │       │       ├─ stage_clear → level +1
    │   │       │       ├─ purchase → gold -price
    │   │       │       └─ User.update_state()
    │   │       │
    │   │       └─ User Update Event 생성 (변경된 속성만)
    │   │           {"#type": "user_set", "properties": {...}}
    │   │
    │   └─ 날짜별 JSONL 파일 저장
    │       └─ logs_20240101.jsonl
    │
    └─ 생성 완료!

┌─────────────────────────────────────────────────────────────┐
│ 5. 업로드 (선택사항)                                          │
└─────────────────────────────────────────────────────────────┘
    │
    └─ LogBus2를 통해 ThinkingEngine으로 업로드
        ├─ logbus_runner.run_upload()
        └─ ThinkingEngine Receiver API
```

---

## 주요 설계 결정

### 1. 하드코딩 제거 전략

#### 문제점
- 게임 산업에 특화된 하드코딩 (`level`, `gold`, `XP`)
- 이커머스/SaaS로 확장 시 코드 대량 수정 필요
- 택소노미 변경 시 코드와 동기화 필요

#### 해결책
```
하드코딩된 예시 제거
    ↓
플레이스홀더 기반 프롬프트
    ↓
AI가 실제 택소노미 분석
    ↓
산업별 적절한 규칙 자동 생성
```

**Before**:
```python
# 하드코딩
if event_name == "stage_clear":
    user.level += 1
    user.gold += 100
```

**After**:
```python
# AI 규칙 기반
updates = property_update_engine.update_user_properties(user, event_name, event_props)
# AI가 분석: stage_clear → level +1, gold +100
```

---

### 2. Segment Analysis 중심 설계

모든 데이터 생성은 **세그먼트별 차별화**를 기반으로 합니다.

```
UserSegment
    ↓
AI segment_analysis
    ├─ property_ranges (세그먼트별 속성 범위)
    ├─ event_sequence (전형적인 행동 흐름)
    └─ event_probabilities (이벤트 발생 확률)
    ↓
현실적인 행동 패턴
```

#### 세그먼트별 특성

| 세그먼트 | 속성 범위 | 주요 이벤트 | 행동 특성 |
|----------|----------|-------------|----------|
| NEW_USER | level 1-5 | tutorial, onboarding | 높은 튜토리얼 완료율, 낮은 전환율 |
| ACTIVE_USER | level 20-60 | 일반 게임플레이 | 균형잡힌 활동, 보통 전환율 |
| POWER_USER | level 100-150 | 고급 콘텐츠, 구매 | 높은 활동량, 높은 구매율 |
| CHURNING_USER | 중간 | 짧은 세션 | 감소하는 활동량 |
| RETURNING_USER | 중간 | 복귀 보상 | 재참여 패턴 |

---

### 3. Event Sequence vs Probabilities

두 가지 방식을 모두 지원하되, **event_sequence를 우선**합니다.

```python
# 1순위: event_sequence (있으면 100% 따름)
ai_event_sequence = self._get_ai_event_sequence(user.segment)
if ai_event_sequence:
    return self._select_from_sequence(ai_event_sequence, session_duration, user)

# 2순위: event_probabilities (폴백)
ai_event_probs = self._get_ai_event_probabilities(user.segment)
return self._select_by_probabilities(ai_event_probs, available_events)
```

**이유**:
- 튜토리얼, 퍼널 등은 순서가 중요
- 순서가 없는 일반 이벤트는 확률로 처리

---

### 4. 생명주기 기반 이벤트 필터링

유저가 모든 이벤트를 즉시 할 수 없도록 생명주기 제약을 적용합니다.

```python
# LifecycleRulesEngine
INSTALLED → 앱 시작, 회원가입만
FIRST_SESSION → 튜토리얼, 온보딩만
ONBOARDING_STARTED → 튜토리얼 계속
ONBOARDING_COMPLETED → 기본 기능
ACTIVE → 대부분 이벤트
ADVANCED → 모든 이벤트 (PvP, Raid 등)
```

**효과**:
- 신규 유저가 갑자기 고급 콘텐츠 플레이하는 비현실적 상황 방지
- 자연스러운 유저 성장 흐름 구현

---

### 5. 캐싱 전략

#### 캐시 무효화 조건
1. 택소노미 변경 (이벤트/속성 추가/삭제/수정)
2. AI 제공자 변경 (OpenAI ↔ Claude)
3. 제품 정보 변경 (industry, platform, product_name)

#### 캐시 저장 위치
```
.cache/
├── analysis_{hash}_{provider}_{product}.json
└── update_patterns_{hash}_{provider}_{product}.json
```

#### 수동 캐시 초기화
```bash
# 전체 캐시 삭제
rm -rf .cache/

# 또는 orchestrator가 자동 초기화 (매 실행마다)
orchestrator.execute() → cache_manager.clear()
```

---

### 6. Faker 폴백 메커니즘

AI가 모든 속성을 분석할 수 없으므로, Faker를 폴백으로 사용합니다.

#### 지원 패턴 (40+)

| 패턴 | Faker 메서드 | 예시 |
|------|-------------|------|
| name, user_name, player_name | name() | "홍길동" |
| email, user_email | email() | "hong@example.com" |
| phone, mobile, tel | phone_number() | "010-1234-5678" |
| address, user_address | address() | "서울특별시 강남구..." |
| company, organization | company() | "삼성전자" |
| job, occupation | job() | "소프트웨어 엔지니어" |
| date, birth_date | date() | "1990-01-01" |
| url, website | url() | "https://example.com" |
| color | color_name() | "blue" |
| country, nation | country() | "South Korea" |

#### 다국어 지원

```python
# country 속성 기반 locale 자동 선택
if country == "KR":
    faker = Faker('ko_KR')  # 한국 이름/주소
elif country == "JP":
    faker = Faker('ja_JP')  # 일본 이름/주소
elif country == "US":
    faker = Faker('en_US')  # 영어 이름/주소
```

---

### 7. 속성 업데이트 엔진

이벤트 발생 시 유저 속성을 자동으로 업데이트하여 **상태 일관성**을 유지합니다.

#### AI 분석 예시

```json
{
  "stage_clear": {
    "level": {"type": "increment", "value": 1},
    "gold": {"type": "increment", "value": 100},
    "xp": {"type": "increment", "value": 50}
  },
  "purchase": {
    "gold": {"type": "decrement", "value": "{{price}}"},
    "total_purchases": {"type": "increment", "value": 1},
    "total_spent": {"type": "increment", "value": "{{price}}"}
  }
}
```

#### 적용 방식

```python
# 이벤트 발생
event_name = "stage_clear"
event_properties = {"stage_id": "1-5", "clear_time": 120}

# 속성 업데이트
updates = property_update_engine.update_user_properties(
    user, event_name, event_properties
)
# updates = {"level": 16, "gold": 1100, "xp": 850}

# User_set 이벤트 생성
{
  "#type": "user_set",
  "#account_id": "user_123",
  "#time": "2024-01-01 14:30:25",
  "properties": updates
}
```

---

## 성능 및 비용 최적화

### AI API 호출 최소화

```
초기 분석: 1회 AI 호출
    ↓
캐싱: .cache/에 저장
    ↓
이후 실행: 캐시 로드 (AI 호출 0회)
    ↓
속성 생성: 규칙 기반 (AI 호출 0회)
    ↓
결과: 수만 개 이벤트 생성해도 AI 호출은 최초 1회만!
```

### 비용 비교

| 시나리오 | AI 호출 횟수 | 예상 비용 | 소요 시간 |
|----------|-------------|----------|----------|
| 첫 실행 (1000 유저, 7일) | 1회 | ~$0.10 | ~15초 |
| 캐시 히트 (동일 조건) | 0회 | $0 | ~2초 |
| 10,000 이벤트 생성 | 0회 | $0 | ~3초 |
| 100,000 이벤트 생성 | 0회 | $0 | ~30초 |

**총 비용**: 1회 분석 비용 (~$0.10) → 무한 생성

---

## 확장 가능성

### 1. 새로운 산업 추가

**코드 수정 불필요!** 택소노미만 정의하면 자동 지원.

```bash
# 새로운 산업 (예: 헬스케어 앱)
python -m data_generator.main interactive

# 입력:
# - Industry: health_fitness
# - Taxonomy: healthcare_events.xlsx

# AI가 자동으로:
# - workout_count, calories_burned, heart_rate 등 속성 분석
# - workout_start → workout_end 시퀀스 파악
# - POWER_USER: 높은 workout_count, 낮은 heart_rate (건강함)
```

### 2. 커스텀 세그먼트

현재는 6개 고정 세그먼트이지만, 향후 커스텀 세그먼트 지원 예정:

```python
custom_segments = [
    "weekend_warriors",    # 주말에만 활동
    "early_morning_users", # 새벽 활동
    "high_spenders",       # 고액 결제자
]
```

### 3. Real-time Feedback Loop

생성된 데이터의 통계를 분석하여 AI 규칙 개선:

```
생성된 데이터
    ↓
통계 분석 (평균, 분산, 분포)
    ↓
AI에게 피드백
    ↓
규칙 재생성
    ↓
더 현실적인 데이터
```

---

## 문제 해결

### AI 분석 실패

**증상**: "AI 분석 실패, 기본 규칙 사용" 메시지

**원인**:
- API 키 오류
- 네트워크 문제
- AI 응답 JSON 파싱 실패

**해결**:
1. API 키 확인 (`.env` 또는 대화형 입력)
2. 네트워크 연결 확인
3. JSON 재시도 로직이 3회 시도 (자동)
4. 폴백으로 하드코딩 값 사용 (정상 동작)

### 캐시 무효화

**언제 필요한가?**
- 택소노미 변경 후
- AI 모델 변경 후
- 이상한 결과가 나올 때 (오래된 캐시 의심)

**방법**:
```bash
# 자동 (orchestrator가 매 실행마다 초기화)
# 또는 수동
rm -rf .cache/
```

### 세그먼트별 데이터 불균형

**증상**: POWER_USER의 레벨이 너무 낮음

**원인**: AI 분석 결과의 segment_analysis가 부적절

**해결**:
1. AI 프롬프트 조정 (ai/claude_client.py, ai/openai_client.py)
2. 또는 하드코딩 폴백 값 조정 (user_generator.py)

### 이벤트 순서 오류

**증상**: tutorial_step3이 tutorial_step1보다 먼저 발생

**원인**: AI의 event_sequence 분석 실패

**해결**:
1. 택소노미에 이벤트 설명 추가 (description 컬럼)
2. event_tag로 이벤트 분류 (튜토리얼, 전투, 구매 등)
3. AI가 더 정확하게 분석 가능

---

## 요약

### 데이터 생성 프로세스

```
1. 택소노미 정의 (Excel/CSV)
   ↓
2. AI 분석 (단 1회)
   - 속성 관계
   - 이벤트 구조
   - 세그먼트별 행동 패턴
   ↓
3. 캐싱 (.cache/)
   ↓
4. 유저 생성
   - 세그먼트 할당
   - 속성 생성 (AI 규칙 적용)
   ↓
5. 행동 시뮬레이션
   - 세션 생성 (시간 패턴)
   - 이벤트 선택 (시퀀스/확률)
   - 생명주기 필터링
   ↓
6. 로그 생성
   - 속성 생성 (AI 규칙 + Faker)
   - 속성 업데이트 (이벤트 영향)
   - ThinkingData 형식 변환
   ↓
7. JSONL 저장 (날짜별 분할)
   ↓
8. LogBus2 업로드 (선택)
```

### 핵심 가치

1. **완전 범용**: 게임/이커머스/SaaS 등 모든 산업 즉시 지원
2. **AI 기반**: 하드코딩 제거, 택소노미 분석으로 자동 규칙 생성
3. **현실적**: 세그먼트별/생명주기별 차별화된 행동 패턴
4. **비용 효율**: 1회 분석으로 무한 생성 (99.97% 비용 절감)
5. **확장 가능**: 새로운 산업/세그먼트 추가 용이

---

## 관련 문서

- [README.md](../README.md) - 전체 프로젝트 소개
- [ThinkingEngine.md](./ThinkingEngine.md) - 데이터 형식 명세
- [Preset Properties.md](./Preset%20Properties.md) - 플랫폼별 프리셋 속성
- [UPLOAD_GUIDE.md](./UPLOAD_GUIDE.md) - LogBus2 업로드 가이드

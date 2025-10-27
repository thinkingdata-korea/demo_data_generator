# Demo Data Generator - Architecture

## Overview

Demo Data Generator는 AI 기반으로 현실적인 제품 분석 데이터를 생성하는 시스템입니다. 게임, 이커머스, SaaS 등 다양한 산업의 택소노미를 분석하여 논리적으로 일관성 있고 현실적인 사용자 행동 데이터를 생성합니다.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Orchestrator                        │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─► 1. Taxonomy Loader (택소노미 로드)
             │
             ├─► 2. AI Client (OpenAI/Claude)
             │
             ├─► 3. IntelligentPropertyGenerator
             │      └─► AI 분석 (한 번만 수행, 캐싱)
             │           ├─ property_constraints
             │           ├─ event_constraints
             │           ├─ property_relationships
             │           ├─ value_ranges
             │           └─ segment_analysis ⭐
             │
             ├─► 4. UserGenerator
             │      └─► AI 분석 결과 활용
             │           └─ 세그먼트별 행동 특성
             │
             ├─► 5. BehaviorEngine
             │      └─► AI 분석 결과 활용
             │           └─ 세그먼트별 이벤트 확률
             │
             └─► 6. LogGenerator
                    └─► 최종 데이터 생성
```

## Core Components

### 1. IntelligentPropertyGenerator

AI를 활용하여 택소노미의 속성들을 분석하고 생성 규칙을 파악하는 핵심 컴포넌트입니다.

#### 주요 기능

- **속성 관계 분석** (`analyze_property_relationships`)
  - 속성 간 논리적 제약조건 파악 (예: carrier → country 매핑)
  - 이벤트별 속성 제약조건 (예: tutorial 이벤트 → 낮은 레벨)
  - 속성 간 의존 관계 (예: level → XP)
  - **세그먼트별 상세 분석** (NEW_USER, ACTIVE_USER, POWER_USER 등)

#### Segment Analysis 구조

```json
{
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
        "tutorial_completed"
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
        "pvp_match",
        "raid_start",
        "guild_activity",
        "purchase"
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

#### 캐싱 시스템

- AI 분석 결과를 디스크에 캐싱하여 재사용
- 캐시 키: `taxonomy_hash + ai_provider + product_info`
- 동일한 택소노미 + AI 모델 조합에서는 캐시 활용하여 API 비용 절감

### 2. UserGenerator

가상 사용자를 생성하는 컴포넌트입니다.

#### AI 분석 결과 활용

**Before (하드코딩):**
```python
characteristics = {
    UserSegment.NEW_USER: {
        "daily_session_count": random.randint(2, 5),
        "session_duration_minutes": random.uniform(10, 25),
        "conversion_probability": 0.02,
    }
}
```

**After (AI 분석 결과 활용):**
```python
def _get_segment_characteristics(self, segment: UserSegment):
    # AI 분석 결과에서 세그먼트별 특성 가져오기
    if self.intelligent_generator and self.intelligent_generator.property_rules:
        segment_analysis = self.intelligent_generator.property_rules.get("segment_analysis", {})
        segment_key = segment.value.upper()

        if segment_key in segment_analysis:
            ai_segment_data = segment_analysis[segment_key]
            # property_ranges에서 실제 값 추출
            # event_probabilities에서 전환 확률 추출
            ...

    # 폴백: 하드코딩된 기본값
    ...
```

#### 개선 효과

- ✅ **산업 무관성**: 게임/이커머스/SaaS 모두 동일한 로직 사용
- ✅ **현실성**: AI가 산업별 특성을 반영하여 적절한 범위 제안
- ✅ **유연성**: 택소노미 변경 시 자동으로 적응

### 3. BehaviorEngine

사용자 행동 패턴을 생성하는 컴포넌트입니다.

#### AI 분석 결과 활용

**Before (하드코딩):**
```python
# ScenarioPattern에서 하드코딩된 우선순위 사용
priorities = ScenarioPattern.get_event_priority_for_scenario(scenario_type)
```

**After (AI 분석 결과 활용):**
```python
def select_events_for_session(self, user, session_duration, behavior_pattern):
    # AI 분석 결과에서 이벤트 확률 가져오기
    ai_event_probs = self._get_ai_event_probabilities(user.segment)

    if ai_event_probs:
        # AI 분석 결과의 event_probabilities 사용
        # NEW_USER: tutorial 이벤트 높은 확률
        # POWER_USER: pvp/raid 이벤트 높은 확률
        ...
    else:
        # 폴백: 하드코딩된 우선순위
        ...
```

#### 개선 효과

- ✅ **세그먼트별 맞춤화**: 각 유저 세그먼트에 적합한 이벤트 선택
- ✅ **현실적인 행동**: AI가 분석한 실제 유저 행동 패턴 반영
- ✅ **이벤트 시퀀스**: event_sequence를 활용하여 자연스러운 흐름 생성

### 4. LogGenerator

최종적으로 이벤트 로그를 생성하는 컴포넌트입니다.

- IntelligentPropertyGenerator를 활용하여 이벤트 속성 생성
- 세그먼트별 제약조건 자동 적용
- 논리적 일관성 유지 (carrier ↔ country, level ↔ XP 등)

## Data Flow

### 1. 초기화 단계

```
Taxonomy Load
    ↓
AI Client 초기화
    ↓
IntelligentPropertyGenerator 생성
    ↓
AI 분석 수행 (analyze_property_relationships)
    ├─ property_constraints
    ├─ event_constraints
    ├─ property_relationships
    ├─ value_ranges
    └─ segment_analysis ⭐
    ↓
캐시 저장 (.cache/ 디렉토리)
```

### 2. 사용자 생성 단계

```
UserGenerator
    ↓
각 세그먼트별로 사용자 생성
    ├─ AI segment_analysis에서 property_ranges 참조
    ├─ 세그먼트별 행동 특성 추출 (session count, duration)
    └─ 세그먼트별 전환 확률 추출
    ↓
User 객체 생성
```

### 3. 행동 생성 단계

```
BehaviorEngine
    ↓
세션별 이벤트 선택
    ├─ AI segment_analysis에서 event_probabilities 참조
    ├─ 세그먼트별 이벤트 우선순위 적용
    └─ lifecycle stage 제약조건 적용
    ↓
이벤트 시퀀스 생성
```

### 4. 로그 생성 단계

```
LogGenerator
    ↓
각 이벤트별 속성 생성
    ├─ AI property_constraints 적용 (논리적 일관성)
    ├─ AI event_constraints 적용 (이벤트별 제약)
    └─ AI property_relationships 적용 (의존성)
    ↓
최종 로그 출력 (JSONL)
```

## Key Design Decisions

### 1. 하드코딩 제거 전략

**문제점:**
- 게임 산업에 특화된 하드코딩 (level, gold, XP 등)
- 이커머스/SaaS로 확장 시 코드 수정 필요
- 택소노미 변경 시 코드 동기화 필요

**해결책:**
- AI가 택소노미를 분석하여 자동으로 규칙 생성
- 산업별 특성을 AI 프롬프트에서 처리
- 코드는 범용적인 로직만 유지

### 2. Segment Analysis 중심 설계

**세그먼트별 차별화:**
- NEW_USER: 낮은 레벨, 튜토리얼 중심, 낮은 구매 확률
- ACTIVE_USER: 중간 레벨, 일반 콘텐츠, 보통 구매 확률
- POWER_USER: 높은 레벨, 엔드게임 콘텐츠, 높은 구매 확률
- CHURNING_USER: 짧은 세션, 낮은 참여도
- RETURNING_USER: 복귀 보상, 재참여 패턴

**AI가 제공하는 정보:**
- property_ranges: 세그먼트별 속성 범위
- event_sequence: 세그먼트별 전형적인 이벤트 흐름
- event_probabilities: 세그먼트별 이벤트 발생 확률

### 3. 캐싱 전략

**이유:**
- AI API 비용 절감
- 생성 속도 향상
- 동일한 택소노미에서 일관성 유지

**캐시 무효화:**
- 택소노미 변경 시
- AI provider 변경 시
- Product info 변경 시

### 4. 폴백 메커니즘

모든 AI 기반 로직은 폴백을 가지고 있습니다:

```python
if self.intelligent_generator and self.intelligent_generator.property_rules:
    # AI 분석 결과 사용
    ...
else:
    # 하드코딩 폴백
    ...
```

이를 통해:
- AI 분석 실패 시에도 동작
- 개발/테스트 환경에서 AI 없이 사용 가능
- 점진적 마이그레이션 가능

## Performance Considerations

### AI API 호출 최소화

- **분석 단계**: 1회 (캐시 미스 시)
- **속성 생성**: IntelligentPropertyGenerator가 규칙 기반으로 생성 (AI 호출 없음)
- **결과**: 수만 개의 이벤트를 생성해도 AI 호출은 초기 1회만

### 캐싱 효과

- 첫 실행: ~10-30초 (AI 분석)
- 이후 실행: ~1-2초 (캐시 로드)
- 캐시 크기: ~50-200KB (JSON 형태)

### 메모리 사용

- AI 분석 결과: 메모리에 상주 (공유)
- User 객체: 필요 시 생성, 사용 후 해제
- 대규모 데이터셋: 스트리밍 방식 지원

## Future Enhancements

### 1. Dynamic Segment Analysis

현재는 6개의 고정 세그먼트를 사용하지만, 향후 커스텀 세그먼트 지원 예정:
- "Weekend warriors"
- "Early morning users"
- "High spenders"

### 2. Event Sequence Modeling

현재는 event_probabilities만 사용하지만, 향후 event_sequence를 마르코프 체인으로 모델링 예정.

### 3. Multi-Modal AI Analysis

- 이미지/비디오 택소노미 분석
- 자연어 이벤트 설명에서 자동 규칙 추출

### 4. Real-time Adaptation

- 생성된 데이터의 통계 분석
- AI 피드백 루프로 규칙 개선

## Troubleshooting

### AI 분석 실패

**증상**: "AI 분석 실패, 기본 규칙 사용" 메시지

**원인**:
- API 키 오류
- 네트워크 문제
- AI 응답 JSON 파싱 실패

**해결**:
- API 키 확인
- 네트워크 연결 확인
- 폴백으로 정상 동작 (하드코딩 값 사용)

### 캐시 무효화

**방법**:
```bash
rm -rf .cache/
```

**시기**:
- 택소노미 변경 후
- AI 모델 변경 후
- 이상한 결과가 나올 때

### 세그먼트별 데이터 불균형

**증상**: POWER_USER의 레벨이 너무 낮음

**원인**: AI 분석 결과의 segment_analysis가 부적절

**해결**:
- AI 프롬프트 조정 (ai/claude_client.py, ai/openai_client.py)
- 또는 하드코딩 폴백 값 조정

## Conclusion

이 아키텍처는 다음 원칙을 따릅니다:

1. **AI-First**: AI가 택소노미를 이해하고 규칙 생성
2. **Industry-Agnostic**: 게임/이커머스/SaaS 모두 동일한 코드
3. **Segment-Aware**: 각 유저 세그먼트에 맞춤화된 데이터
4. **Cacheable**: 비용과 속도 최적화
5. **Fallback-Ready**: AI 없이도 동작 가능

이를 통해 현실적이고 일관성 있는 제품 분석 데이터를 효율적으로 생성할 수 있습니다.

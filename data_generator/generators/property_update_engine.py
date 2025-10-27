"""
범용 이벤트 기반 속성 업데이트 엔진
AI가 택소노미를 분석하여 이벤트 발생 시 유저 속성 업데이트 규칙을 파악
게임, 이커머스, SaaS 등 모든 산업에서 동작
"""
import random
from typing import Dict, Any, Optional, List
import json

from ..ai.base_client import BaseAIClient
from ..models.taxonomy import EventTaxonomy
from ..models.user import User
from ..utils.cache_manager import CacheManager


class PropertyUpdateEngine:
    """
    AI 기반 범용 속성 업데이트 엔진

    이벤트 발생 시 유저 속성을 어떻게 업데이트할지 AI가 분석하여 결정
    - 게임: stage_clear → level +1, gold +100
    - 이커머스: purchase → total_purchases +1, total_spent += amount
    - SaaS: feature_used → usage_count +1, last_used_at = now
    """

    def __init__(
        self,
        ai_client: BaseAIClient,
        taxonomy: EventTaxonomy,
        product_info: Dict[str, Any],
        enable_cache: bool = True
    ):
        self.ai_client = ai_client
        self.taxonomy = taxonomy
        self.product_info = product_info
        self.update_mappings: Optional[Dict[str, Any]] = None
        self.enable_cache = enable_cache
        self.cache_manager = CacheManager() if enable_cache else None

    def analyze_event_update_patterns(self):
        """
        AI를 사용해 이벤트별 유저 속성 업데이트 패턴을 한 번만 분석
        결과를 캐싱하여 재사용
        """
        if self.update_mappings is not None:
            return  # 이미 분석됨

        # 캐시 확인
        if self.cache_manager:
            # 택소노미 해시 계산 (간단하게 이벤트 수로)
            cache_key = f"update_patterns_{len(self.taxonomy.events)}_{self.product_info.get('industry', 'unknown')}"
            cached_mappings = self.cache_manager.load(cache_key)
            if cached_mappings:
                self.update_mappings = cached_mappings
                return

        # 캐시 미스 - AI 분석 수행
        print("  🤖 AI가 이벤트별 유저 속성 업데이트 패턴을 분석하고 있습니다...")

        try:
            # AI 프롬프트 구성
            prompt = self._build_analysis_prompt()

            # AI 호출 (base_client의 공통 메서드 활용)
            # TODO: AI client에 analyze_update_patterns 메서드 추가 필요
            # 임시로 직접 호출
            response = self._call_ai_for_analysis(prompt)

            self.update_mappings = response
            print(f"  ✓ {len(self.update_mappings)}개 이벤트의 업데이트 규칙 파악 완료")

            # 캐시 저장
            if self.cache_manager:
                self.cache_manager.save(cache_key, self.update_mappings, {
                    'event_count': len(self.taxonomy.events),
                    'product_info': self.product_info
                })

        except Exception as e:
            print(f"  ⚠️  AI 분석 실패, 빈 업데이트 규칙 사용: {e}")
            self.update_mappings = {}

    def _build_analysis_prompt(self) -> str:
        """AI 분석을 위한 프롬프트 구성"""
        # 이벤트 정보
        events_info = []
        for event in self.taxonomy.events[:30]:  # 상위 30개만
            events_info.append({
                "name": event.event_name,
                "description": event.event_description or "",
                "properties": [p.name for p in (event.properties or [])]
            })

        # 유저 속성 정보
        user_props_info = [
            {
                "name": prop.name,
                "type": prop.property_type.value if hasattr(prop.property_type, 'value') else str(prop.property_type),
                "description": prop.description or ""
            }
            for prop in self.taxonomy.user_properties
        ]

        # 공통 속성 정보
        common_props_info = [
            {
                "name": prop.name,
                "type": prop.property_type.value if hasattr(prop.property_type, 'value') else str(prop.property_type),
                "description": prop.description or ""
            }
            for prop in self.taxonomy.common_properties
        ]

        prompt = f"""
You are an expert data analyst. Analyze this event taxonomy and determine how user properties should be updated when events occur.

**Product Context:**
- Industry: {self.product_info.get('industry', 'unknown')}
- Platform: {self.product_info.get('platform', 'unknown')}
- Product: {self.product_info.get('product_name', 'unknown')}

**Events:**
{json.dumps(events_info, indent=2, ensure_ascii=False)}

**User Properties:**
{json.dumps(user_props_info, indent=2, ensure_ascii=False)}

**Common Properties (current state):**
{json.dumps(common_props_info, indent=2, ensure_ascii=False)}

**Analysis Required:**
For each event, determine:
1. Which user properties should be updated when this event occurs?
2. How should they be updated? (increment, add, set, formula)
3. Are there any conditions for the update?

**Update Types:**
- "increment": Add 1 to the property (e.g., total_purchases +1)
- "add_from_event": Add a value from the event properties (e.g., total_spent += purchase_amount)
- "set": Set to a specific value or current time
- "formula": Calculate using a formula (e.g., "property_a + property_b * 2")

**Return JSON format:**
{{
    "event_name": {{
        "event_type": "progression|conversion|identity|session|social",
        "updates": {{
            "increment": ["property1", "property2"],
            "add_from_event": {{
                "target_property": "event_property_name"
            }},
            "set": {{
                "property3": "fixed_value_or_current_time"
            }},
            "formula": {{
                "property4": "expression using other properties"
            }}
        }},
        "probability": 1.0,
        "description": "Brief explanation why these updates occur"
    }}
}}

**Important:**
- Only suggest updates that make logical sense for this industry
- Don't assume game-specific properties (level, gold) unless it's a game
- Use generic patterns (counters, timestamps, aggregations)
- Return ONLY valid JSON, no markdown or explanations

Return your analysis:
"""
        return prompt

    def _call_ai_for_analysis(self, prompt: str) -> Dict[str, Any]:
        """AI 호출하여 이벤트별 업데이트 패턴 분석"""
        try:
            # ClaudeClient나 OpenAIClient는 모두 _call_api 메서드를 가지고 있음
            if hasattr(self.ai_client, '_call_api'):
                # 프롬프트를 system과 user로 분리
                system_prompt = """You are an expert in data modeling and event-driven user property updates.
Analyze event taxonomy and determine how user properties should be updated when specific events occur.
Return your response as a JSON object only, without any markdown formatting."""

                # 기존 프롬프트는 user_prompt로 사용
                response = self.ai_client._call_api(system_prompt, prompt)
                return response
            else:
                # 폴백: 빈 결과
                print("  ⚠️  AI client does not have _call_api method")
                return {}

        except Exception as e:
            print(f"  ⚠️  AI 호출 실패: {e}")
            return {}

    def get_updates_for_event(
        self,
        event_name: str,
        user: User,
        event_properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        이벤트에 따른 유저 속성 업데이트 계산 (범용)

        Args:
            event_name: 발생한 이벤트명
            user: 유저 객체
            event_properties: 이벤트 속성들

        Returns:
            업데이트할 유저 속성 딕셔너리
        """
        if not self.update_mappings:
            return {}

        # 이벤트 매핑 찾기
        event_mapping = self.update_mappings.get(event_name)
        if not event_mapping:
            # 부분 매칭 시도 (예: "tutorial_step_1" → "tutorial")
            for pattern, mapping in self.update_mappings.items():
                if pattern in event_name.lower() or event_name.lower() in pattern:
                    event_mapping = mapping
                    break

        if not event_mapping:
            return {}

        # 확률 체크
        probability = event_mapping.get("probability", 1.0)
        if random.random() > probability:
            return {}

        updates = {}
        update_rules = event_mapping.get("updates", {})

        # 1. Increment (속성명만)
        for prop_name in update_rules.get("increment", []):
            current = user.get_state(prop_name, 0)
            updates[prop_name] = current + 1

        # 2. Add from event (이벤트 속성의 값을 더함)
        for target_prop, source_prop in update_rules.get("add_from_event", {}).items():
            if source_prop in event_properties:
                current = user.get_state(target_prop, 0)
                add_value = event_properties[source_prop]
                if isinstance(add_value, (int, float)):
                    updates[target_prop] = current + add_value

        # 3. Set (고정값 또는 특수값)
        for prop_name, value in update_rules.get("set", {}).items():
            if value == "current_time":
                from datetime import datetime
                updates[prop_name] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif value == "event_name":
                updates[prop_name] = event_name
            else:
                updates[prop_name] = value

        # 4. Formula (동적 계산)
        for prop_name, formula in update_rules.get("formula", {}).items():
            try:
                # 안전하게 공식 평가
                result = self._evaluate_formula(formula, user, event_properties)
                if result is not None:
                    updates[prop_name] = result
            except Exception as e:
                # 공식 평가 실패 시 무시
                pass

        return updates

    def _evaluate_formula(
        self,
        formula: str,
        user: User,
        event_properties: Dict[str, Any]
    ) -> Optional[Any]:
        """
        안전하게 공식 평가

        예: "total_spent + purchase_amount"
            → user.get_state("total_spent") + event_properties["purchase_amount"]
        """
        try:
            # 컨텍스트 준비
            context = {}

            # 유저 상태의 모든 속성
            for prop in self.taxonomy.common_properties:
                value = user.get_state(prop.name)
                if value is not None:
                    context[prop.name] = value

            for prop in self.taxonomy.user_properties:
                value = user.get_state(prop.name)
                if value is not None:
                    context[prop.name] = value

            # 이벤트 속성 추가
            context.update(event_properties)

            # 허용된 변수만 사용 (숫자만)
            allowed_vars = {k: v for k, v in context.items() if isinstance(v, (int, float))}

            # 공식에서 변수 치환
            eval_formula = formula
            for var_name, var_value in allowed_vars.items():
                if var_name in eval_formula:
                    eval_formula = eval_formula.replace(var_name, str(var_value))

            # 단순 계산 (eval 사용하되 안전하게)
            result = eval(eval_formula, {"__builtins__": {}}, {})

            if isinstance(result, (int, float)):
                return result

        except Exception:
            pass

        return None

    def should_update_for_event(self, event_name: str) -> bool:
        """이 이벤트가 유저 속성 업데이트를 유발하는지 확인"""
        if not self.update_mappings:
            return False

        # 직접 매칭
        if event_name in self.update_mappings:
            return True

        # 부분 매칭
        for pattern in self.update_mappings.keys():
            if pattern in event_name.lower() or event_name.lower() in pattern:
                return True

        return False

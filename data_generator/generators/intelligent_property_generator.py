"""
AI 기반 지능형 속성값 생성기
택소노미와 제품 정보를 분석하여 현실적인 값을 생성
"""
import random
from typing import Dict, Any, Optional, List
from datetime import datetime
from faker import Faker

from ..ai.base_client import BaseAIClient
from ..models.user import User
from ..utils.cache_manager import CacheManager


class IntelligentPropertyGenerator:
    """AI 분석 기반 속성값 생성기"""

    def __init__(
        self,
        ai_client: BaseAIClient,
        taxonomy_properties: List[Any],
        product_info: Dict[str, Any],
        enable_cache: bool = True,
        event_names: List[str] = None,
    ):
        self.ai_client = ai_client
        self.product_info = product_info
        self.property_rules: Optional[Dict[str, Any]] = None
        self.enable_cache = enable_cache
        self.cache_manager = CacheManager() if enable_cache else None
        self.event_names = event_names or []

        # 택소노미 속성을 딕셔너리 형태로 변환
        self.taxonomy_props_dict = []
        for prop in taxonomy_properties:
            self.taxonomy_props_dict.append({
                "name": prop.name,
                "property_type": prop.property_type.value if hasattr(prop.property_type, 'value') else str(prop.property_type),
                "description": getattr(prop, 'description', '')
            })

        # Faker 인스턴스 초기화 (다양한 locale 지원)
        self.faker_instances = {
            "ko_KR": Faker('ko_KR'),
            "en_US": Faker('en_US'),
            "ja_JP": Faker('ja_JP'),
            "zh_CN": Faker('zh_CN'),
        }
        # 기본 Faker (영어)
        self.default_faker = self.faker_instances["en_US"]

    def analyze_properties(self):
        """
        AI를 사용해 속성 관계와 생성 규칙을 한 번만 분석
        결과를 캐싱하여 재사용
        """
        if self.property_rules is not None:
            return  # 이미 분석됨

        # 캐시 확인
        if self.cache_manager:
            taxonomy_hash = self.cache_manager.compute_taxonomy_hash(self.taxonomy_props_dict)
            ai_provider = getattr(self.ai_client, 'model', 'unknown').split('-')[0]  # "claude" or "gpt"
            cache_key = self.cache_manager.get_cache_key(taxonomy_hash, ai_provider, self.product_info)

            cached_rules = self.cache_manager.load(cache_key)
            if cached_rules:
                self.property_rules = cached_rules
                return

        # 캐시 미스 - AI 분석 수행
        print("  🤖 AI가 택소노미를 분석하여 속성 간 관계를 파악하고 있습니다...")

        try:
            raw_rules = self.ai_client.analyze_property_relationships(
                taxonomy_properties=self.taxonomy_props_dict,
                product_info=self.product_info,
                event_names=self.event_names
            )

            # AI 응답 검증 및 필터링
            self.property_rules = self._validate_and_filter_ai_response(raw_rules)

            print(f"  ✓ {len(self.property_rules.get('value_ranges', {}))}개 속성의 생성 규칙 파악 완료")

            # 캐시 저장
            if self.cache_manager:
                metadata = {
                    'taxonomy_properties_count': len(self.taxonomy_props_dict),
                    'ai_provider': ai_provider,
                    'product_info': self.product_info
                }
                self.cache_manager.save(cache_key, self.property_rules, metadata)

        except Exception as e:
            print(f"  ⚠️  AI 분석 실패, 기본 규칙 사용: {e}")
            self.property_rules = {
                "property_relationships": {},
                "value_ranges": {},
                "generation_strategy": {}
            }

    def _validate_and_filter_ai_response(self, ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI 응답을 검증하고 택소노미에 없는 속성을 필터링

        Args:
            ai_response: AI가 반환한 원본 분석 결과

        Returns:
            검증 및 필터링된 분석 결과
        """
        # 택소노미에 실제 있는 속성명 목록
        valid_properties = set(prop['name'] for prop in self.taxonomy_props_dict)

        filtered_response = {}
        invalid_props_found = []

        # value_ranges 필터링
        if 'value_ranges' in ai_response:
            filtered_ranges = {}
            for prop_name, prop_range in ai_response['value_ranges'].items():
                if prop_name in valid_properties:
                    filtered_ranges[prop_name] = prop_range
                else:
                    invalid_props_found.append(prop_name)
            filtered_response['value_ranges'] = filtered_ranges

        # property_relationships 필터링
        if 'property_relationships' in ai_response:
            filtered_relationships = {}
            for prop_name, relationship in ai_response['property_relationships'].items():
                if prop_name in valid_properties:
                    filtered_relationships[prop_name] = relationship
                else:
                    invalid_props_found.append(prop_name)
            filtered_response['property_relationships'] = filtered_relationships

        # generation_strategy 필터링
        if 'generation_strategy' in ai_response:
            filtered_strategy = {}
            for prop_name, strategy in ai_response['generation_strategy'].items():
                if prop_name in valid_properties:
                    filtered_strategy[prop_name] = strategy
                else:
                    invalid_props_found.append(prop_name)
            filtered_response['generation_strategy'] = filtered_strategy

        # segment_analysis, property_constraints, event_constraints는 그대로 유지
        for key in ['segment_analysis', 'property_constraints', 'event_constraints']:
            if key in ai_response:
                filtered_response[key] = ai_response[key]

        # 경고 출력
        if invalid_props_found:
            unique_invalid = set(invalid_props_found)
            print(f"  ⚠️  택소노미에 없는 속성 {len(unique_invalid)}개 필터링됨: {', '.join(list(unique_invalid)[:5])}{'...' if len(unique_invalid) > 5 else ''}")

        return filtered_response

    def generate_property_value(
        self,
        prop_name: str,
        prop_type: str,
        user: Optional[User],
        event_name: Optional[str] = None,
        session_events: Optional[List[str]] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        AI 분석 결과를 기반으로 현실적인 속성값 생성

        Args:
            prop_name: 속성명
            prop_type: 속성 타입 (string, number, boolean, etc.)
            user: 유저 객체 (컨텍스트, None 가능 - 초기 생성 시)
            event_name: 이벤트명 (선택)
            session_events: 현재 세션의 이벤트 시퀀스 (선택)
            additional_context: 추가 컨텍스트 (preset properties 등)
        """
        # AI 분석 결과가 없으면 먼저 분석
        if self.property_rules is None:
            self.analyze_properties()

        # 생성 전략 확인
        strategy = self.property_rules.get("generation_strategy", {}).get(prop_name, "random-simple")

        if strategy == "ai-contextual":
            # AI가 컨텍스트를 고려해야 한다고 판단한 속성
            return self._generate_with_ai_context(prop_name, prop_type, user, event_name, additional_context)
        elif strategy == "rule-based":
            # 규칙 기반 생성 (AI가 제공한 규칙 사용)
            return self._generate_with_rules(prop_name, prop_type, user, additional_context)
        else:
            # 단순 랜덤 (AI 범위 정보 + 이벤트 컨텍스트 활용)
            return self._generate_simple(prop_name, prop_type, event_name, session_events, additional_context)

    def _generate_with_rules(self, prop_name: str, prop_type: str, user: Optional[User], additional_context: Optional[Dict[str, Any]] = None) -> Any:
        """규칙 기반 생성 (AI가 파악한 관계 활용)"""
        relationships = self.property_rules.get("property_relationships", {}).get(prop_name, {})
        depends_on = relationships.get("depends_on", [])
        formula_hint = relationships.get("formula_hint", "")

        # 의존하는 속성들의 값 가져오기
        context_values = {}
        if user is not None:
            for dep_prop in depends_on:
                value = user.get_state(dep_prop)
                if value is not None:
                    context_values[dep_prop] = value

        # additional_context 병합 (preset properties 등)
        if additional_context:
            context_values.update(additional_context)

        # AI가 제안한 공식 힌트 활용
        if formula_hint and context_values:
            try:
                # 간단한 공식 평가 (안전하게)
                result = self._safe_eval_formula(formula_hint, context_values)
                if result is not None:
                    return result
            except:
                pass

        # 공식 적용 실패 시 범위 기반 생성
        return self._generate_with_range(prop_name, prop_type, context_values)

    def _generate_with_range(self, prop_name: str, prop_type: str, context: Dict[str, Any]) -> Any:
        """AI가 제공한 범위 정보 + 컨텍스트(engagement_tier)를 활용한 생성"""
        value_range = self.property_rules.get("value_ranges", {}).get(prop_name, {})

        if prop_type == "number":
            min_val = value_range.get("min", 0)
            max_val = value_range.get("max", 1000)
            typical = value_range.get("typical", (min_val + max_val) / 2)

            # engagement_tier에 따라 범위 조정
            engagement_tier = context.get("engagement_tier", "medium")

            # tier별 범위 조정 계수
            tier_adjustments = {
                "very_low": 0.1,   # 최소값 근처 (10%)
                "low": 0.3,        # 하위 (30%)
                "medium": 0.5,     # 중간 (50%)
                "high": 0.7,       # 상위 (70%)
                "very_high": 0.9   # 최상위 (90%)
            }

            adjustment = tier_adjustments.get(engagement_tier, 0.5)

            # 정규분포를 사용하되, 평균을 tier에 맞게 조정
            import random
            if max_val > min_val:
                # tier에 따라 평균 위치 조정
                adjusted_mean = min_val + (max_val - min_val) * adjustment

                # 표준편차를 범위의 1/6로 설정
                std_dev = (max_val - min_val) / 6
                value = random.gauss(adjusted_mean, std_dev)
                value = max(min_val, min(max_val, value))  # 범위 제한

                # 정수형이면 반올림
                if isinstance(min_val, int) and isinstance(max_val, int):
                    return int(round(value))
                return round(value, 2)
            return typical

        elif prop_type == "string":
            # 컨텍스트를 고려한 문자열 생성
            return self._generate_contextual_string(prop_name, context)

        elif prop_type == "boolean":
            # AI 범위 정보에 확률이 있으면 활용
            probability = value_range.get("typical", 0.5)
            return random.random() < probability

        else:
            return self._generate_simple(prop_name, prop_type, additional_context=context)

    def _generate_contextual_string(self, prop_name: str, context: Dict[str, Any]) -> str:
        """
        컨텍스트를 고려한 현실적인 문자열 생성
        AI example_values 우선, 없으면 Faker 기반 폴백
        """
        prop_lower = prop_name.lower()

        # AI 분석 결과에서 예시 값 가져오기
        value_range = self.property_rules.get("value_ranges", {}).get(prop_name, {})
        example_values = value_range.get("example_values", [])

        # AI가 제공한 예시 값이 있으면 그 중에서 랜덤 선택
        if example_values and isinstance(example_values, list) and len(example_values) > 0:
            return random.choice(example_values)

        # Faker 폴백: 컨텍스트에서 국가 정보 추출하여 locale 선택
        faker = self._select_faker_by_context(context)

        # 예시 값이 없을 경우 Faker 기반 폴백 로직

        # 1. 사람 관련 속성
        if any(keyword in prop_lower for keyword in ["name", "user_name", "username", "nick", "nickname", "player_name"]):
            return faker.name()

        elif "email" in prop_lower or "mail" in prop_lower:
            return faker.email()

        elif "phone" in prop_lower or "mobile" in prop_lower or "tel" in prop_lower:
            return faker.phone_number()

        # 2. 위치 관련 속성
        elif "address" in prop_lower or "street" in prop_lower:
            return faker.address().replace('\n', ', ')  # 한 줄로

        elif "city" in prop_lower:
            return faker.city()

        elif "state" in prop_lower or "province" in prop_lower:
            return faker.state() if hasattr(faker, 'state') else faker.city()

        elif "country" in prop_lower:
            return faker.country()

        elif "zipcode" in prop_lower or "postal" in prop_lower:
            return faker.postcode()

        # 3. 조직/비즈니스 관련 속성
        elif "company" in prop_lower or "organization" in prop_lower or "business" in prop_lower:
            return faker.company()

        elif "job" in prop_lower or "occupation" in prop_lower or "position" in prop_lower:
            return faker.job()

        # 4. 웹 관련 속성
        elif "url" in prop_lower or "website" in prop_lower or "link" in prop_lower:
            return faker.url()

        elif "domain" in prop_lower:
            return faker.domain_name()

        elif "ip" in prop_lower and "address" in prop_lower:
            return faker.ipv4()

        # 5. 텍스트 관련 속성
        elif "description" in prop_lower or "bio" in prop_lower or "about" in prop_lower:
            return faker.text(max_nb_chars=100)

        elif "comment" in prop_lower or "message" in prop_lower or "content" in prop_lower:
            return faker.sentence()

        elif "title" in prop_lower or "subject" in prop_lower:
            return faker.sentence(nb_words=random.randint(3, 8)).rstrip('.')

        # 6. 날짜/시간 관련 (문자열로)
        elif "date" in prop_lower and "time" not in prop_lower:
            return faker.date()

        elif "datetime" in prop_lower or ("date" in prop_lower and "time" in prop_lower):
            return faker.date_time().strftime("%Y-%m-%d %H:%M:%S")

        # 7. ID 타입 (기존 로직 유지)
        elif "id" in prop_lower or "identifier" in prop_lower or "uuid" in prop_lower:
            # UUID 스타일
            if "uuid" in prop_lower:
                return faker.uuid4()
            # 컨텍스트 기반 ID
            else:
                level = context.get("level", context.get("tmp_level", random.randint(1, 50)))
                return f"{prop_name}_{level}_{random.randint(1000, 9999)}"

        # 8. 색상
        elif "color" in prop_lower or "colour" in prop_lower:
            return faker.color_name()

        # 9. 카테고리/태그 (범용)
        elif "category" in prop_lower or "tag" in prop_lower or "type" in prop_lower:
            # 산업 무관하게 범용적인 카테고리명
            categories = ["category_a", "category_b", "category_c", "premium", "standard", "basic", "featured", "popular"]
            return random.choice(categories)

        # 10. 채널/소스 (마케팅 관련)
        elif "channel" in prop_lower or "source" in prop_lower or "medium" in prop_lower:
            channels = ["organic", "direct", "referral", "social", "email", "paid_search", "display", "affiliate"]
            return random.choice(channels)

        # 11. 기타 - 범용 포맷
        else:
            return f"{prop_name}_{random.randint(1, 100)}"

    def _select_faker_by_context(self, context: Dict[str, Any]) -> Faker:
        """
        컨텍스트에서 국가/지역 정보를 추출하여 적절한 Faker locale 선택
        """
        # 컨텍스트에서 국가 정보 찾기
        country = context.get("country", context.get("#country", "")).lower()

        # 국가별 locale 매핑
        if "korea" in country or "kr" in country:
            return self.faker_instances["ko_KR"]
        elif "japan" in country or "jp" in country:
            return self.faker_instances["ja_JP"]
        elif "china" in country or "cn" in country:
            return self.faker_instances["zh_CN"]
        else:
            # 기본값: 영어 (미국)
            return self.default_faker

    def _generate_simple(
        self,
        prop_name: str,
        prop_type: str,
        event_name: Optional[str] = None,
        session_events: Optional[List[str]] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """단순 랜덤 생성 (AI 범위 정보 + 이벤트 컨텍스트 활용)"""
        value_range = self.property_rules.get("value_ranges", {}).get(prop_name, {})

        # 이벤트별 제약조건 확인 (AI가 분석한 결과)
        event_constraint = None
        if event_name:
            event_constraints = self.property_rules.get("event_constraints", {})
            # 이벤트 이름 매칭 (정확한 매칭 또는 부분 매칭)
            for event_pattern, constraints in event_constraints.items():
                if event_pattern in event_name.lower() or event_name.lower() in event_pattern:
                    event_constraint = constraints.get(prop_name)
                    break

        # 컨텍스트 준비 (additional_context 포함)
        context = additional_context.copy() if additional_context else {}

        if prop_type == "string":
            # 예시 값 확인
            example_values = value_range.get("example_values", [])
            if example_values and isinstance(example_values, list) and len(example_values) > 0:
                return random.choice(example_values)
            return self._generate_contextual_string(prop_name, context)
        elif prop_type == "number":
            # 이벤트 제약조건이 있으면 우선 적용
            if event_constraint and isinstance(event_constraint, dict):
                min_val = event_constraint.get("min", value_range.get("min", 1))
                max_val = event_constraint.get("max", value_range.get("max", 1000))
            else:
                min_val = value_range.get("min", 1)
                max_val = value_range.get("max", 1000)
            return random.randint(int(min_val), int(max_val))
        elif prop_type == "boolean":
            return random.choice([True, False])
        elif prop_type == "time":
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif prop_type == "list":
            # AI 예시 값이 있으면 그 중에서 1-3개 선택
            example_values = value_range.get("example_values", [])
            if example_values and isinstance(example_values, list) and len(example_values) > 0:
                count = random.randint(1, min(3, len(example_values)))
                return random.sample(example_values, count)
            # 폴백: 간단한 리스트
            return [self._generate_simple(f"{prop_name}_item", "string") for _ in range(random.randint(1, 3))]
        elif prop_type == "object":
            return {"field_1": "value_1", "field_2": "value_2"}
        else:
            return None

    def _generate_with_ai_context(
        self,
        prop_name: str,
        prop_type: str,
        user: Optional[User],
        event_name: Optional[str],
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        AI에게 컨텍스트를 제공하고 값을 생성 요청
        (비용이 높으므로 중요한 속성에만 사용)
        """
        # 캐싱을 위해 일단 규칙 기반으로 폴백
        # 실제 운영에서는 배치로 여러 속성을 한 번에 요청하는 것이 효율적
        return self._generate_with_rules(prop_name, prop_type, user, additional_context)

    def _safe_eval_formula(self, formula: str, context: Dict[str, Any]) -> Optional[float]:
        """
        안전하게 공식 평가
        예: "level * 1000" -> context["level"] * 1000
        """
        try:
            # 허용된 변수와 연산만 사용
            allowed_vars = {k: v for k, v in context.items() if isinstance(v, (int, float))}

            # 간단한 산술 연산만 허용
            # eval 대신 ast.literal_eval 사용하거나 파싱
            import ast
            import operator

            # 지원하는 연산자
            ops = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
            }

            # 공식에서 변수 치환
            for var_name, var_value in allowed_vars.items():
                if var_name in formula:
                    formula = formula.replace(var_name, str(var_value))

            # 단순 계산
            try:
                result = eval(formula, {"__builtins__": {}}, {})
                if isinstance(result, (int, float)):
                    return result
            except:
                pass

        except Exception:
            pass

        return None

    def should_update_user_property(
        self,
        event_name: str,
        user: User,
        event_properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        이벤트 기반으로 업데이트할 유저 속성 결정
        AI 분석 결과(property_relationships)를 활용하여 동적으로 판단
        """
        updates = {}

        if not self.property_rules:
            return updates

        # AI 분석 결과에서 관계 정보 가져오기
        relationships = self.property_rules.get("property_relationships", {})

        # AI가 분석한 속성 간 관계를 기반으로 업데이트
        for prop_name, prop_info in relationships.items():
            # AI가 이 속성이 다른 속성에 의존한다고 판단한 경우
            depends_on = prop_info.get("depends_on", [])
            formula_hint = prop_info.get("formula_hint", "")

            if depends_on and formula_hint:
                # 공식 힌트가 있으면 계산
                context_values = {}
                for dep_prop in depends_on:
                    # 이벤트 속성에서 먼저 찾고, 없으면 유저 상태에서
                    value = event_properties.get(dep_prop)
                    if value is None:
                        value = user.get_state(dep_prop)
                    if value is not None:
                        context_values[dep_prop] = value

                if context_values:
                    new_value = self._safe_eval_formula(formula_hint, context_values)
                    if new_value is not None:
                        updates[prop_name] = new_value

        return updates

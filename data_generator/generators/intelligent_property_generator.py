"""
AI 기반 지능형 속성값 생성기
택소노미와 제품 정보를 분석하여 현실적인 값을 생성
"""
import random
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..ai.base_client import BaseAIClient
from ..models.user import User


class IntelligentPropertyGenerator:
    """AI 분석 기반 속성값 생성기"""

    def __init__(
        self,
        ai_client: BaseAIClient,
        taxonomy_properties: List[Any],
        product_info: Dict[str, Any],
    ):
        self.ai_client = ai_client
        self.product_info = product_info
        self.property_rules: Optional[Dict[str, Any]] = None

        # 택소노미 속성을 딕셔너리 형태로 변환
        self.taxonomy_props_dict = []
        for prop in taxonomy_properties:
            self.taxonomy_props_dict.append({
                "name": prop.name,
                "property_type": prop.property_type.value if hasattr(prop.property_type, 'value') else str(prop.property_type),
                "description": getattr(prop, 'description', '')
            })

    def analyze_properties(self):
        """
        AI를 사용해 속성 관계와 생성 규칙을 한 번만 분석
        결과를 캐싱하여 재사용
        """
        if self.property_rules is not None:
            return  # 이미 분석됨

        print("  🤖 AI가 택소노미를 분석하여 속성 간 관계를 파악하고 있습니다...")

        try:
            self.property_rules = self.ai_client.analyze_property_relationships(
                taxonomy_properties=self.taxonomy_props_dict,
                product_info=self.product_info
            )
            print(f"  ✓ {len(self.property_rules.get('value_ranges', {}))}개 속성의 생성 규칙 파악 완료")
        except Exception as e:
            print(f"  ⚠️  AI 분석 실패, 기본 규칙 사용: {e}")
            self.property_rules = {
                "property_relationships": {},
                "value_ranges": {},
                "generation_strategy": {}
            }

    def generate_property_value(
        self,
        prop_name: str,
        prop_type: str,
        user: User,
        event_name: Optional[str] = None
    ) -> Any:
        """
        AI 분석 결과를 기반으로 현실적인 속성값 생성

        Args:
            prop_name: 속성명
            prop_type: 속성 타입 (string, number, boolean, etc.)
            user: 유저 객체 (컨텍스트)
            event_name: 이벤트명 (선택)
        """
        # AI 분석 결과가 없으면 먼저 분석
        if self.property_rules is None:
            self.analyze_properties()

        # 생성 전략 확인
        strategy = self.property_rules.get("generation_strategy", {}).get(prop_name, "random-simple")

        if strategy == "ai-contextual":
            # AI가 컨텍스트를 고려해야 한다고 판단한 속성
            return self._generate_with_ai_context(prop_name, prop_type, user, event_name)
        elif strategy == "rule-based":
            # 규칙 기반 생성 (AI가 제공한 규칙 사용)
            return self._generate_with_rules(prop_name, prop_type, user)
        else:
            # 단순 랜덤 (AI 범위 정보 활용)
            return self._generate_simple(prop_name, prop_type)

    def _generate_with_rules(self, prop_name: str, prop_type: str, user: User) -> Any:
        """규칙 기반 생성 (AI가 파악한 관계 활용)"""
        relationships = self.property_rules.get("property_relationships", {}).get(prop_name, {})
        depends_on = relationships.get("depends_on", [])
        formula_hint = relationships.get("formula_hint", "")

        # 의존하는 속성들의 값 가져오기
        context_values = {}
        for dep_prop in depends_on:
            context_values[dep_prop] = user.get_state(dep_prop)

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
        """AI가 제공한 범위 정보를 활용한 생성"""
        value_range = self.property_rules.get("value_ranges", {}).get(prop_name, {})

        if prop_type == "number":
            min_val = value_range.get("min", 0)
            max_val = value_range.get("max", 1000)
            typical = value_range.get("typical", (min_val + max_val) / 2)

            # 정규분포를 사용해 typical 주변값 생성
            import random
            if max_val > min_val:
                # 표준편차를 범위의 1/6로 설정 (68% 가 typical 근처)
                std_dev = (max_val - min_val) / 6
                value = random.gauss(typical, std_dev)
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
            return self._generate_simple(prop_name, prop_type)

    def _generate_contextual_string(self, prop_name: str, context: Dict[str, Any]) -> str:
        """컨텍스트를 고려한 문자열 생성"""
        prop_lower = prop_name.lower()

        # AI 분석 결과에서 예시 값 가져오기
        value_range = self.property_rules.get("value_ranges", {}).get(prop_name, {})
        example_values = value_range.get("example_values", [])

        # AI가 제공한 예시 값이 있으면 그 중에서 랜덤 선택
        if example_values and isinstance(example_values, list) and len(example_values) > 0:
            return random.choice(example_values)

        # 예시 값이 없을 경우 폴백 로직
        # ID 타입
        if "id" in prop_lower or "identifier" in prop_lower:
            # 컨텍스트에서 레벨 정보가 있으면 활용
            level = context.get("level", context.get("tmp_level", random.randint(1, 50)))
            return f"{prop_name}_{level}_{random.randint(1000, 9999)}"

        # 이름 타입
        elif "name" in prop_lower or "title" in prop_lower:
            # 산업별 적절한 이름 생성 (폴백)
            industry = self.product_info.get("industry", "")
            if "game" in industry.lower():
                return f"{prop_name}_{random.randint(1, 100)}"
            elif "ecommerce" in industry.lower():
                return f"Product_{random.randint(1, 1000)}"
            elif "finance" in industry.lower() or "fintech" in industry.lower():
                return f"Account_{random.randint(10000, 99999)}"
            else:
                return f"{prop_name}_{random.randint(1, 100)}"

        # 기타
        else:
            return f"value_{random.randint(1, 100)}"

    def _generate_simple(self, prop_name: str, prop_type: str) -> Any:
        """단순 랜덤 생성 (AI 범위 정보 활용)"""
        value_range = self.property_rules.get("value_ranges", {}).get(prop_name, {})

        if prop_type == "string":
            # 예시 값 확인
            example_values = value_range.get("example_values", [])
            if example_values and isinstance(example_values, list) and len(example_values) > 0:
                return random.choice(example_values)
            return self._generate_contextual_string(prop_name, {})
        elif prop_type == "number":
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
        user: User,
        event_name: Optional[str]
    ) -> Any:
        """
        AI에게 컨텍스트를 제공하고 값을 생성 요청
        (비용이 높으므로 중요한 속성에만 사용)
        """
        # 캐싱을 위해 일단 규칙 기반으로 폴백
        # 실제 운영에서는 배치로 여러 속성을 한 번에 요청하는 것이 효율적
        return self._generate_with_rules(prop_name, prop_type, user)

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
        AI 분석 결과를 활용하여 동적으로 판단
        """
        updates = {}

        # AI 분석 결과에서 관계 정보 가져오기
        relationships = self.property_rules.get("property_relationships", {})

        # 이벤트명을 기반으로 업데이트할 속성 추론
        event_lower = event_name.lower()

        for prop_name, prop_info in relationships.items():
            relationship = prop_info.get("relationship", "").lower()

            # 이벤트와 관련된 속성인지 판단
            if any(keyword in event_lower for keyword in ["complete", "clear", "finish"]):
                if any(keyword in prop_name.lower() for keyword in ["level", "stage", "progress"]):
                    # 완료 이벤트 -> 레벨/진행도 증가
                    current = user.get_state(prop_name, 1)
                    if isinstance(current, (int, float)):
                        updates[prop_name] = current + 1

            elif any(keyword in event_lower for keyword in ["purchase", "buy", "payment"]):
                if any(keyword in prop_name.lower() for keyword in ["total", "spend", "revenue"]):
                    # 구매 이벤트 -> 총액 증가
                    amount = event_properties.get("price", event_properties.get("amount", 0))
                    current = user.get_state(prop_name, 0)
                    if isinstance(amount, (int, float)) and isinstance(current, (int, float)):
                        updates[prop_name] = current + amount

        return updates

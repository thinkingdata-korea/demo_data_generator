"""
User generator for creating virtual users.
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from faker import Faker

from ..models.user import User, UserSegment, LifecycleStage
from ..models.taxonomy import EventTaxonomy
from ..config.config_schema import DataGeneratorConfig, ScenarioType


class UserGenerator:
    """Generates virtual users based on configuration"""

    def __init__(
        self,
        config: DataGeneratorConfig,
        taxonomy: EventTaxonomy,
        intelligent_generator=None  # Optional[IntelligentPropertyGenerator]
    ):
        self.config = config
        self.taxonomy = taxonomy
        self.intelligent_generator = intelligent_generator  # AI 기반 속성 생성기

        # 다양한 locale의 Faker 인스턴스 초기화
        self.faker_instances = {
            "ko_KR": Faker('ko_KR'),
            "en_US": Faker('en_US'),
            "ja_JP": Faker('ja_JP'),
            "zh_CN": Faker('zh_CN'),
        }

        if config.seed:
            random.seed(config.seed)
            Faker.seed(config.seed)

    def generate_users(self) -> List[User]:
        """Generate all users based on configuration"""
        # AI 분석 초기화 (한 번만 실행)
        if self.intelligent_generator and self.intelligent_generator.property_rules is None:
            self.intelligent_generator.analyze_properties()

        total_users = self.config.get_total_users_estimate()
        users = []

        # Calculate user counts per scenario
        scenario_counts = self._calculate_scenario_distribution(total_users)

        # Generate users for each scenario
        for scenario_config in self.config.scenarios:
            count = scenario_counts[scenario_config.scenario_type]

            # Determine segment based on scenario type or custom behavior
            if scenario_config.is_custom():
                # For custom scenarios, use a default segment (can be customized later)
                segment = UserSegment.ACTIVE_USER
            else:
                segment = self._scenario_to_segment(scenario_config.scenario_type)

            for _ in range(count):
                user = self._create_user(segment)
                # Store scenario key in user metadata for behavior engine
                user.metadata["scenario_key"] = scenario_config.get_scenario_key()
                users.append(user)

        return users

    def _calculate_scenario_distribution(self, total_users: int) -> Dict[ScenarioType, int]:
        """Calculate how many users per scenario"""
        distribution = {}

        for scenario_config in self.config.scenarios:
            count = int(total_users * scenario_config.percentage / 100)
            distribution[scenario_config.scenario_type] = count

        # Handle rounding errors
        total_assigned = sum(distribution.values())
        if total_assigned < total_users:
            # Add remaining to most common scenario
            largest_scenario = max(distribution, key=distribution.get)
            distribution[largest_scenario] += (total_users - total_assigned)

        return distribution

    def _scenario_to_segment(self, scenario_type: ScenarioType) -> UserSegment:
        """Map scenario type to user segment"""
        mapping = {
            ScenarioType.NORMAL: UserSegment.ACTIVE_USER,
            ScenarioType.NEW_USER_ONBOARDING: UserSegment.NEW_USER,
            ScenarioType.POWER_USER: UserSegment.POWER_USER,
            ScenarioType.CHURNING_USER: UserSegment.CHURNING_USER,
            ScenarioType.CHURNED_USER: UserSegment.CHURNED_USER,
            ScenarioType.RETURNING_USER: UserSegment.RETURNING_USER,
            ScenarioType.CONVERTING_USER: UserSegment.ACTIVE_USER,  # Active with high conversion
        }
        return mapping.get(scenario_type, UserSegment.ACTIVE_USER)

    def _create_user(self, segment: UserSegment) -> User:
        """Create a single user"""
        # Generate IDs
        distinct_id = self._generate_distinct_id()
        account_id = self._generate_account_id() if segment != UserSegment.NEW_USER else None

        # Determine first seen time
        # Users should have appeared before the data generation period
        days_before_start = self._get_days_before_start(segment)
        first_seen = self.config.start_date - timedelta(days=days_before_start)

        # Convert date to datetime
        first_seen_dt = datetime.combine(first_seen, datetime.min.time())
        first_seen_dt = first_seen_dt.replace(
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )

        # Behavior characteristics based on segment
        characteristics = self._get_segment_characteristics(segment)

        # Initialize user state with realistic values (COMMON properties)
        initial_state = self._generate_initial_state(segment, days_before_start)

        # Generate USER properties (택소노미의 유저 속성)
        user_properties = self._generate_user_properties(segment, days_before_start, first_seen_dt)

        # 생명주기 단계 결정 (segment 기반)
        lifecycle_stage = self._determine_initial_lifecycle_stage(segment, days_before_start)

        user = User(
            account_id=account_id,
            distinct_id=distinct_id,
            segment=segment,
            lifecycle_stage=lifecycle_stage,
            current_state=initial_state,
            daily_session_count=characteristics["daily_session_count"],
            session_duration_minutes=characteristics["session_duration_minutes"],
            conversion_probability=characteristics["conversion_probability"],
            first_seen_time=first_seen_dt,
            last_seen_time=first_seen_dt,
            metadata={
                "days_before_start": days_before_start,
                "user_properties": user_properties,  # USER properties 저장
            }
        )

        return user

    def _generate_initial_state(self, segment: UserSegment, days_before_start: int) -> Dict[str, Any]:
        """
        Generate initial user state with realistic values based on taxonomy
        AI 기반 생성으로 산업 무관하게 동작
        """
        state = {}

        # Segment를 범용적인 "참여도" 개념으로 변환
        engagement_tier = self._get_engagement_tier_for_segment(segment)

        # 각 공통 속성 생성
        for prop in self.taxonomy.common_properties:
            prop_name = prop.name
            prop_type = prop.property_type.value

            # AI 생성기가 있으면 사용
            if self.intelligent_generator:
                # 임시 유저 컨텍스트 (최소 정보)
                temp_user_context = {
                    "segment": segment.value,
                    "engagement_tier": engagement_tier,
                    "days_since_install": days_before_start
                }

                value = self.intelligent_generator.generate_property_value(
                    prop_name=prop_name,
                    prop_type=prop_type,
                    user=None,  # 아직 User 객체 생성 전이므로 None
                    event_name=None,
                    session_events=None,
                    additional_context=temp_user_context
                )
            else:
                # 폴백: 타입별 기본값만 생성
                value = self._generate_default_value_by_type(prop_type)

            state[prop_name] = value

        return state

    def _get_engagement_tier_for_segment(self, segment: UserSegment) -> str:
        """
        Segment를 범용적인 참여도 등급으로 변환
        게임/이커머스/SaaS 모두에서 의미 있는 개념
        """
        tier_mapping = {
            UserSegment.NEW_USER: "very_low",       # 막 시작
            UserSegment.CHURNED_USER: "low",        # 이탈
            UserSegment.CHURNING_USER: "low",       # 이탈 위험
            UserSegment.ACTIVE_USER: "medium",      # 일반 활동
            UserSegment.RETURNING_USER: "medium",   # 복귀
            UserSegment.POWER_USER: "very_high",    # 파워 유저
        }
        return tier_mapping.get(segment, "medium")

    def _generate_default_value_by_type(self, prop_type: str) -> Any:
        """
        타입별 기본값 생성 (AI 없을 때만 사용)
        아무 가정도 하지 않음 - 단순히 타입에 맞는 빈 값
        """
        if prop_type == "string":
            return None  # AI가 생성하도록
        elif prop_type == "number":
            return 0  # 중립적인 기본값
        elif prop_type == "boolean":
            return False
        elif prop_type == "list":
            return []
        elif prop_type == "time":
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif prop_type == "object":
            return {}
        else:
            return None

    def _generate_distinct_id(self) -> str:
        """Generate a distinct ID (device ID)"""
        # Format: device_uuid
        return f"device_{uuid.uuid4().hex[:16]}"

    def _generate_account_id(self) -> str:
        """Generate an account ID"""
        # Format: user_uuid
        return f"user_{uuid.uuid4().hex[:16]}"

    def _get_days_before_start(self, segment: UserSegment) -> int:
        """Get how many days before start date the user first appeared"""
        ranges = {
            UserSegment.NEW_USER: (0, 3),  # Very recent
            UserSegment.ACTIVE_USER: (7, 90),  # Regular users
            UserSegment.POWER_USER: (30, 180),  # Long-term users
            UserSegment.CHURNING_USER: (14, 60),  # Recent but declining
            UserSegment.CHURNED_USER: (30, 180),  # Haven't been active
            UserSegment.RETURNING_USER: (60, 365),  # Older users coming back
        }

        min_days, max_days = ranges.get(segment, (7, 90))
        return random.randint(min_days, max_days)

    def _get_segment_characteristics(self, segment: UserSegment) -> Dict[str, Any]:
        """
        Get behavior characteristics for a segment from AI analysis
        AI 분석 결과 필수 - 없으면 에러
        """
        if not self.intelligent_generator or not self.intelligent_generator.property_rules:
            raise ValueError("IntelligentPropertyGenerator is required for user generation")

        segment_analysis = self.intelligent_generator.property_rules.get("segment_analysis", {})
        segment_key = segment.value.upper()  # "NEW_USER", "ACTIVE_USER", etc.

        if segment_key not in segment_analysis:
            # 세그먼트 분석 결과가 없으면 기본 범위 사용
            print(f"  ⚠️  Warning: No AI analysis for segment {segment_key}, using generic ranges")
            return {
                "daily_session_count": random.randint(1, 3),
                "session_duration_minutes": random.uniform(5, 15),
                "conversion_probability": 0.05,
            }

        ai_segment_data = segment_analysis[segment_key]
        property_ranges = ai_segment_data.get("property_ranges", {})

        # AI 분석 결과에서 세션/플레이타임 정보 추출
        daily_session_count = self._extract_value_from_range(
            property_ranges.get("daily_session_count", property_ranges.get("session_count", {}))
        )
        session_duration_minutes = self._extract_value_from_range(
            property_ranges.get("session_duration_minutes", property_ranges.get("playtime_minutes", {}))
        )

        # conversion/purchase 확률 추출
        event_probs = ai_segment_data.get("event_probabilities", {})
        conversion_probability = event_probs.get("purchase", event_probs.get("conversion", 0.05))

        return {
            "daily_session_count": daily_session_count if daily_session_count is not None else random.randint(1, 3),
            "session_duration_minutes": session_duration_minutes if session_duration_minutes is not None else random.uniform(5, 15),
            "conversion_probability": conversion_probability,
        }

    def _extract_value_from_range(self, range_dict: Dict[str, Any]) -> Optional[float]:
        """
        AI 분석 결과의 범위 정보에서 값을 추출
        range_dict: {"min": x, "max": y, "mean": z} 형태
        """
        if not range_dict or not isinstance(range_dict, dict):
            return None

        mean = range_dict.get("mean")
        min_val = range_dict.get("min")
        max_val = range_dict.get("max")

        if mean is not None:
            # mean 값 주변에서 정규분포로 생성
            if min_val is not None and max_val is not None:
                std_dev = (max_val - min_val) / 6
                value = random.gauss(mean, std_dev)
                return max(min_val, min(max_val, value))
            return mean
        elif min_val is not None and max_val is not None:
            # min/max만 있으면 균등분포
            if isinstance(min_val, int) and isinstance(max_val, int):
                return random.randint(min_val, max_val)
            return random.uniform(min_val, max_val)

        return None

    def _generate_user_properties(
        self,
        segment: UserSegment,
        days_before_start: int,
        first_seen_time: datetime
    ) -> Dict[str, Any]:
        """
        Generate USER properties (택소노미의 유저 속성)
        ThinkingEngine의 user_set 이벤트로 설정되는 속성들

        AI 기반 생성으로 산업 무관하게 동작
        """
        user_props = {}

        # Segment를 범용적인 참여도로 변환
        engagement_tier = self._get_engagement_tier_for_segment(segment)

        # 택소노미의 user_properties를 순회하며 생성
        for prop in self.taxonomy.user_properties:
            prop_name = prop.name
            prop_type = prop.property_type.value

            # AI 생성기가 있으면 사용
            if self.intelligent_generator:
                # 컨텍스트 준비
                temp_user_context = {
                    "segment": segment.value,
                    "engagement_tier": engagement_tier,
                    "days_since_install": days_before_start,
                    "first_seen_time": first_seen_time.isoformat()
                }

                value = self.intelligent_generator.generate_property_value(
                    prop_name=prop_name,
                    prop_type=prop_type,
                    user=None,  # 아직 User 객체 없음
                    event_name=None,
                    session_events=None,
                    additional_context=temp_user_context
                )
            else:
                # 폴백: 타입별 기본값
                if prop_type == "time":
                    value = first_seen_time.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    value = self._generate_default_value_by_type(prop_type)

            user_props[prop_name] = value

        return user_props

    def _determine_initial_lifecycle_stage(self, segment: UserSegment, days_before_start: int) -> LifecycleStage:
        """
        유저 segment와 가입 시점에 따라 초기 생명주기 단계 결정

        Args:
            segment: 유저 세그먼트
            days_before_start: 데이터 생성 시작일 기준 과거 며칠

        Returns:
            초기 생명주기 단계
        """
        if segment == UserSegment.NEW_USER:
            # 신규 유저: 설치만 했거나 첫 세션 시작
            if days_before_start == 0:
                return LifecycleStage.INSTALLED
            elif days_before_start <= 1:
                return LifecycleStage.FIRST_SESSION
            else:
                # 1일 이상 지났으면 온보딩 진행 중이거나 완료
                return random.choice([
                    LifecycleStage.ONBOARDING_STARTED,
                    LifecycleStage.ONBOARDING_COMPLETED
                ])

        elif segment == UserSegment.ACTIVE_USER:
            # 활성 유저: 온보딩 완료 또는 일반 활동
            if days_before_start <= 7:
                return LifecycleStage.ONBOARDING_COMPLETED
            else:
                return LifecycleStage.ACTIVE

        elif segment == UserSegment.POWER_USER:
            # 파워 유저: 온보딩 완료 후 고급 단계
            if days_before_start <= 14:
                return LifecycleStage.ACTIVE
            else:
                return LifecycleStage.ADVANCED

        elif segment == UserSegment.CHURNING_USER:
            # 이탈 위험 유저: 활성 단계였지만 이탈 중
            return LifecycleStage.ACTIVE

        elif segment == UserSegment.CHURNED_USER:
            # 이탈 유저: 과거에는 활성이었음
            return LifecycleStage.ACTIVE

        elif segment == UserSegment.RETURNING_USER:
            # 복귀 유저: 과거에 활성이었고 다시 돌아옴
            return LifecycleStage.ACTIVE

        # 기본값
        return LifecycleStage.ACTIVE

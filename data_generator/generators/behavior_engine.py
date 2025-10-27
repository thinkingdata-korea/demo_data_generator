"""
Scenario-based behavior engine using AI.
"""
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..ai.base_client import BaseAIClient
from ..models.taxonomy import EventTaxonomy
from ..models.user import User, UserSegment, LifecycleStage
from ..patterns.time_patterns import TimePatternGenerator
from ..patterns.lifecycle_rules import LifecycleRulesEngine


class BehaviorEngine:
    """Generates realistic user behaviors based on scenarios"""

    def __init__(
        self,
        ai_client: BaseAIClient,
        taxonomy: EventTaxonomy,
        product_info: Dict[str, Any],
        custom_scenarios: Optional[Dict[str, str]] = None,
        intelligent_generator=None,  # Optional[IntelligentPropertyGenerator]
    ):
        self.ai_client = ai_client
        self.taxonomy = taxonomy
        self.product_info = product_info
        self.behavior_cache: Dict[str, Dict[str, Any]] = {}
        self.custom_scenarios = custom_scenarios or {}  # {scenario_key: custom_behavior_text}
        self.intelligent_generator = intelligent_generator  # AI 분석 결과 접근용

        # 생명주기 규칙 엔진 (하드코딩 + AI)
        self.lifecycle_rules = LifecycleRulesEngine()

    def get_behavior_pattern(self, scenario_type: str) -> Dict[str, Any]:
        """
        Get or generate behavior pattern for a scenario.
        Uses caching to avoid repeated AI calls.
        Supports both predefined and custom scenarios.
        """
        if scenario_type in self.behavior_cache:
            return self.behavior_cache[scenario_type]

        # Check if this is a custom scenario
        is_custom = scenario_type.startswith("custom_")

        # Get event names for AI context
        event_names = self.taxonomy.get_all_event_names()

        if is_custom:
            # Custom scenario - use AI to generate pattern from description
            custom_description = self.custom_scenarios.get(scenario_type, "")

            if not custom_description:
                # Fallback to normal if no description
                return self.get_behavior_pattern("normal")

            # Generate AI pattern for custom scenario
            merged_pattern = self.ai_client.generate_custom_behavior_pattern(
                product_info=self.product_info,
                custom_scenario_description=custom_description,
                event_taxonomy={"events": event_names},
            )
        else:
            # Predefined scenario - use AI to generate pattern
            merged_pattern = self.ai_client.generate_behavior_pattern(
                product_info=self.product_info,
                scenario=scenario_type,
                event_taxonomy={"events": event_names},
            )

        # Cache the result
        self.behavior_cache[scenario_type] = merged_pattern

        return merged_pattern

    def generate_daily_sessions(
        self,
        user: User,
        date: datetime,
        behavior_pattern: Dict[str, Any],
    ) -> List[tuple]:
        """
        Generate session times for a user on a specific day.

        Returns:
            List of (start_time, end_time) tuples
        """
        # Check if user should be active today
        if not TimePatternGenerator.should_user_be_active(
            date=date,
            user_segment=user.segment.value,
            base_daily_probability=behavior_pattern.get("activity_probability", 0.7)
        ):
            return []

        # Get session count for the day
        session_range = behavior_pattern.get("daily_session_range", (1, 3))
        session_count = random.randint(session_range[0], session_range[1])

        if session_count == 0:
            return []

        # Get session duration
        duration_range = behavior_pattern.get("session_duration_range", (5, 15))
        avg_duration = random.uniform(duration_range[0], duration_range[1])

        # Get time pattern
        time_pattern_type = behavior_pattern.get("time_pattern", "normal")
        hourly_dist = TimePatternGenerator.get_hourly_distribution(time_pattern_type)

        # Generate session times
        sessions = TimePatternGenerator.generate_session_times(
            date=date,
            session_count=session_count,
            hourly_dist=hourly_dist,
            session_duration_minutes=avg_duration,
        )

        return sessions

    def select_events_for_session(
        self,
        user: User,
        session_duration_minutes: float,
        behavior_pattern: Dict[str, Any],
    ) -> List[str]:
        """
        Select which events should occur during a session.
        AI가 분석한 event_sequence를 우선 사용하고, 없으면 확률 기반으로 폴백

        Returns:
            List of event names in order
        """
        # AI 분석 결과에서 이벤트 시퀀스 가져오기
        ai_event_sequence = self._get_ai_event_sequence(user.segment)

        # AI 시퀀스가 있으면 우선 사용 (순서 보장)
        if ai_event_sequence:
            sequence_events = self._select_from_sequence(ai_event_sequence, session_duration_minutes, user)
            if sequence_events:  # 유효한 시퀀스가 있으면 반환
                return sequence_events

        # 폴백: 기존 확률 기반 방식
        events = []

        # Always start with app_start
        if any("start" in e.event_name.lower() for e in self.taxonomy.events):
            start_events = [e.event_name for e in self.taxonomy.events if "start" in e.event_name.lower()]
            if start_events:
                events.append(start_events[0])

        # Calculate how many events based on session duration
        # Rough estimate: 1 event per 2-3 minutes
        event_count = max(1, int(session_duration_minutes / 2.5))

        # Get event engagement multiplier
        engagement = behavior_pattern.get("event_engagement", 1.0)
        event_count = int(event_count * engagement)

        # AI 분석 결과에서 이벤트 확률 가져오기
        ai_event_probs = self._get_ai_event_probabilities(user.segment)

        # Filter events (exclude system events + 생명주기 제약)
        available_events = []
        for e in self.taxonomy.events:
            # 시스템 이벤트 제외
            if e.event_tag and "시스템" in e.event_tag:
                continue

            # 생명주기 단계에서 허용되는 이벤트인지 확인
            if self.lifecycle_rules.is_event_allowed_in_lifecycle(e.event_name, user.lifecycle_stage):
                available_events.append(e)

        # 허용된 이벤트가 없으면 기본 이벤트만
        if not available_events:
            # app_end만 추가하고 반환
            if any("end" in e.event_name.lower() for e in self.taxonomy.events):
                end_events = [e.event_name for e in self.taxonomy.events if "end" in e.event_name.lower()]
                if end_events:
                    events.append(end_events[0])
            return events

        # Calculate weights based on AI event probabilities
        weights = []
        for event in available_events:
            weight = 1.0

            if ai_event_probs:
                # 이벤트명 정확 매칭
                if event.event_name in ai_event_probs:
                    weight = ai_event_probs[event.event_name]
                # 부분 매칭 (패턴)
                else:
                    matched = False
                    for pattern, prob in ai_event_probs.items():
                        if pattern.lower() in event.event_name.lower():
                            weight = prob
                            matched = True
                            break
                    # 매칭 안되면 기본 가중치 유지 (1.0)

            weights.append(weight)

        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]

            # Select events
            selected = random.choices(
                available_events,
                weights=weights,
                k=min(event_count, len(available_events))
            )

            events.extend([e.event_name for e in selected])

        # Always end with app_end
        if any("end" in e.event_name.lower() for e in self.taxonomy.events):
            end_events = [e.event_name for e in self.taxonomy.events if "end" in e.event_name.lower()]
            if end_events:
                events.append(end_events[0])

        return events

    def should_trigger_conversion(
        self,
        user: User,
        behavior_pattern: Dict[str, Any],
    ) -> bool:
        """Determine if a conversion event should trigger"""
        conversion_prob = behavior_pattern.get("conversion_probability", 0.05)
        return random.random() < conversion_prob

    def should_user_churn(
        self,
        user: User,
        behavior_pattern: Dict[str, Any],
        days_since_start: int,
    ) -> bool:
        """Determine if a user should churn"""
        churn_prob = behavior_pattern.get("churn_probability", 0.001)

        # Increase churn probability over time for churning users
        if user.segment == UserSegment.CHURNING_USER:
            churn_prob = min(churn_prob * (1 + days_since_start * 0.1), 0.5)

        return random.random() < churn_prob

    def _get_ai_event_probabilities(self, user_segment: UserSegment) -> Optional[Dict[str, float]]:
        """
        AI 분석 결과에서 세그먼트별 이벤트 확률 가져오기

        Returns:
            Dict[event_name, probability] or None if not available
        """
        if not self.intelligent_generator or not self.intelligent_generator.property_rules:
            return None

        segment_analysis = self.intelligent_generator.property_rules.get("segment_analysis", {})
        segment_key = user_segment.value.upper()  # "NEW_USER", "ACTIVE_USER", etc.

        if segment_key not in segment_analysis:
            return None

        event_probabilities = segment_analysis[segment_key].get("event_probabilities", {})

        if not event_probabilities:
            return None

        return event_probabilities

    def _get_ai_event_sequence(self, user_segment: UserSegment) -> Optional[List[str]]:
        """
        AI 분석 결과에서 세그먼트별 이벤트 시퀀스 가져오기

        Returns:
            List of event names in typical order, or None if not available
        """
        if not self.intelligent_generator or not self.intelligent_generator.property_rules:
            return None

        segment_analysis = self.intelligent_generator.property_rules.get("segment_analysis", {})
        segment_key = user_segment.value.upper()

        if segment_key not in segment_analysis:
            return None

        event_sequence = segment_analysis[segment_key].get("event_sequence", [])

        if not event_sequence:
            return None

        return event_sequence

    def _select_from_sequence(
        self,
        base_sequence: List[str],
        session_duration_minutes: float,
        user: User
    ) -> List[str]:
        """
        AI가 제공한 이벤트 시퀀스 기반으로 세션 이벤트 선택
        약간의 변형을 추가하여 자연스러움 유지

        Args:
            base_sequence: AI가 분석한 기본 이벤트 순서
            session_duration_minutes: 세션 지속 시간
            user: 유저 객체

        Returns:
            이벤트명 리스트 (순서 보장)
        """
        # 세션 시간에 따라 시퀀스에서 몇 개를 가져올지 결정
        event_count = max(2, int(session_duration_minutes / 2.5))
        event_count = min(event_count, len(base_sequence))

        # 생명주기 단계에서 허용되는 이벤트만 필터링
        allowed_sequence = []
        for event_name in base_sequence:
            if self.lifecycle_rules.is_event_allowed_in_lifecycle(event_name, user.lifecycle_stage):
                allowed_sequence.append(event_name)

        if not allowed_sequence:
            # 허용된 이벤트가 없으면 빈 리스트 반환 (폴백 로직이 처리)
            return []

        # 시퀀스의 앞부분부터 선택 (자연스러운 흐름)
        selected_events = allowed_sequence[:event_count]

        # 30% 확률로 일부 이벤트를 스킵하거나 반복 (자연스러운 변형)
        if random.random() < 0.3 and len(selected_events) > 2:
            # 중간 이벤트 하나를 스킵
            skip_idx = random.randint(1, len(selected_events) - 2)
            selected_events = selected_events[:skip_idx] + selected_events[skip_idx + 1:]

        return selected_events

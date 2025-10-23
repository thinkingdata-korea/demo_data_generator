"""
Scenario-based behavior engine using AI.
"""
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..ai.base_client import BaseAIClient
from ..models.taxonomy import EventTaxonomy
from ..models.user import User, UserSegment
from ..patterns.scenarios import ScenarioPattern
from ..patterns.time_patterns import TimePatternGenerator


class BehaviorEngine:
    """Generates realistic user behaviors based on scenarios"""

    def __init__(
        self,
        ai_client: BaseAIClient,
        taxonomy: EventTaxonomy,
        product_info: Dict[str, Any],
        custom_scenarios: Optional[Dict[str, str]] = None,
    ):
        self.ai_client = ai_client
        self.taxonomy = taxonomy
        self.product_info = product_info
        self.behavior_cache: Dict[str, Dict[str, Any]] = {}
        self.custom_scenarios = custom_scenarios or {}  # {scenario_key: custom_behavior_text}

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

        if is_custom:
            # Custom scenario - use AI to generate pattern from description
            custom_description = self.custom_scenarios.get(scenario_type, "")

            if not custom_description:
                # Fallback to normal if no description
                return self.get_behavior_pattern("normal")

            # Get event names for AI context
            event_names = self.taxonomy.get_all_event_names()

            # Generate AI pattern for custom scenario
            ai_pattern = self.ai_client.generate_custom_behavior_pattern(
                product_info=self.product_info,
                custom_scenario_description=custom_description,
                event_taxonomy={"events": event_names[:50]},
            )

            # Use AI pattern directly for custom scenarios
            merged_pattern = ai_pattern
        else:
            # Predefined scenario - use base + AI enhancement
            base_pattern = ScenarioPattern.get_scenario_characteristics(scenario_type)

            # Get event names for AI context
            event_names = self.taxonomy.get_all_event_names()

            # Generate AI-enhanced behavior pattern
            ai_pattern = self.ai_client.generate_behavior_pattern(
                product_info=self.product_info,
                scenario=scenario_type,
                event_taxonomy={"events": event_names[:50]},
            )

            # Merge base and AI patterns
            merged_pattern = {**base_pattern, **ai_pattern}

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

        Returns:
            List of event names in order
        """
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

        # Get event priorities for this scenario
        scenario_type = user.segment.value
        priorities = ScenarioPattern.get_event_priority_for_scenario(scenario_type)

        # Filter events (exclude system events)
        available_events = [
            e for e in self.taxonomy.events
            if not e.event_tag or "시스템" not in e.event_tag
        ]

        # Calculate weights based on priorities
        weights = []
        for event in available_events:
            weight = 1.0
            # Check if event name matches any priority pattern
            for pattern, multiplier in priorities.items():
                if pattern != "default" and pattern.lower() in event.event_name.lower():
                    weight = multiplier
                    break
            else:
                weight = priorities.get("default", 1.0)
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

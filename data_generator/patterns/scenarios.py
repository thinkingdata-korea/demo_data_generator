"""
User behavior scenarios and patterns.
"""
from typing import Dict, Any, List
from enum import Enum


class ScenarioPattern:
    """Defines behavior patterns for different user scenarios"""

    @staticmethod
    def get_scenario_characteristics(scenario_type: str) -> Dict[str, Any]:
        """
        Get behavior characteristics for a scenario.

        Returns:
            Dictionary with:
            - daily_session_range: (min, max) sessions per day
            - session_duration_range: (min, max) minutes per session
            - activity_probability: Base probability of being active each day
            - conversion_probability: Probability of conversion events
            - time_pattern: Time distribution pattern type
            - event_engagement: Multiplier for event frequency
        """
        scenarios = {
            "normal": {
                "daily_session_range": (1, 3),
                "session_duration_range": (5, 15),
                "activity_probability": 0.7,
                "conversion_probability": 0.05,
                "time_pattern": "normal",
                "event_engagement": 1.0,
                "churn_probability": 0.001,  # 0.1% per day
            },
            "new_user_onboarding": {
                "daily_session_range": (2, 5),
                "session_duration_range": (10, 25),
                "activity_probability": 0.9,
                "conversion_probability": 0.02,
                "time_pattern": "normal",
                "event_engagement": 1.5,  # Higher engagement initially
                "churn_probability": 0.05,  # 5% churn after first few days
            },
            "power_user": {
                "daily_session_range": (5, 15),
                "session_duration_range": (20, 60),
                "activity_probability": 0.95,
                "conversion_probability": 0.15,
                "time_pattern": "power_user",
                "event_engagement": 2.0,
                "churn_probability": 0.0001,  # Very low churn
            },
            "churning_user": {
                "daily_session_range": (0, 2),
                "session_duration_range": (2, 8),
                "activity_probability": 0.3,
                "conversion_probability": 0.01,
                "time_pattern": "normal",
                "event_engagement": 0.5,
                "churn_probability": 0.02,  # 2% per day
            },
            "churned_user": {
                "daily_session_range": (0, 1),
                "session_duration_range": (1, 5),
                "activity_probability": 0.05,
                "conversion_probability": 0.001,
                "time_pattern": "normal",
                "event_engagement": 0.2,
                "churn_probability": 0.0,  # Already churned
            },
            "returning_user": {
                "daily_session_range": (2, 6),
                "session_duration_range": (10, 30),
                "activity_probability": 0.8,
                "conversion_probability": 0.08,
                "time_pattern": "normal",
                "event_engagement": 1.3,
                "churn_probability": 0.005,  # 0.5% per day
            },
            "converting_user": {
                "daily_session_range": (3, 8),
                "session_duration_range": (15, 40),
                "activity_probability": 0.85,
                "conversion_probability": 0.8,  # High conversion intent
                "time_pattern": "normal",
                "event_engagement": 1.5,
                "churn_probability": 0.001,
            },
        }

        return scenarios.get(scenario_type, scenarios["normal"])

    @staticmethod
    def get_event_priority_for_scenario(scenario_type: str) -> Dict[str, float]:
        """
        Get event priority multipliers for a scenario.
        Higher values mean the event is more likely for this scenario.

        Returns:
            Dictionary mapping event patterns to multipliers
        """
        priorities = {
            "new_user_onboarding": {
                "signup": 5.0,
                "tutorial": 5.0,
                "onboard": 5.0,
                "first": 3.0,
                "install": 5.0,
                "default": 1.0,
            },
            "power_user": {
                "purchase": 3.0,
                "iap": 3.0,
                "complete": 2.0,
                "unlock": 2.0,
                "upgrade": 2.5,
                "achieve": 2.0,
                "default": 1.5,
            },
            "churning_user": {
                "error": 2.0,
                "fail": 1.5,
                "cancel": 2.0,
                "default": 0.5,
            },
            "churned_user": {
                "start": 0.5,
                "end": 1.0,
                "default": 0.2,
            },
            "converting_user": {
                "view": 2.0,
                "click": 2.0,
                "add": 2.5,
                "cart": 3.0,
                "checkout": 4.0,
                "purchase": 5.0,
                "subscribe": 5.0,
                "default": 1.2,
            },
        }

        return priorities.get(scenario_type, {"default": 1.0})

    @staticmethod
    def get_funnel_sequences() -> Dict[str, List[str]]:
        """
        Get common funnel sequences (event flows).

        Returns:
            Dictionary mapping funnel names to event sequences
        """
        return {
            "onboarding": [
                "te_app_install",
                "te_app_start",
                "user_signup",
                "tutorial_start",
                "tutorial_complete",
            ],
            "purchase": [
                "product_view",
                "add_to_cart",
                "checkout_start",
                "payment_info_enter",
                "purchase_complete",
            ],
            "content_consumption": [
                "te_app_start",
                "content_browse",
                "content_view",
                "content_complete",
                "te_app_end",
            ],
            "social_interaction": [
                "profile_view",
                "follow_user",
                "post_create",
                "post_share",
                "comment_add",
            ],
        }

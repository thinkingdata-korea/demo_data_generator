"""
Base AI client interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseAIClient(ABC):
    """Abstract base class for AI clients"""

    @abstractmethod
    def generate_behavior_pattern(
        self,
        product_info: Dict[str, Any],
        scenario: str,
        event_taxonomy: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate realistic user behavior patterns based on product and scenario.

        Args:
            product_info: Product/app information (industry, platform, description)
            scenario: User scenario type (normal, power_user, churning, etc.)
            event_taxonomy: Event taxonomy information

        Returns:
            Behavior pattern dictionary with:
            - daily_session_count: Average sessions per day
            - session_duration_minutes: Average session duration
            - event_frequencies: Frequency distribution for each event
            - event_sequences: Common event sequences/flows
            - time_patterns: Activity patterns by time of day
        """
        pass

    @abstractmethod
    def generate_event_properties(
        self,
        event_name: str,
        event_schema: Dict[str, Any],
        user_context: Dict[str, Any],
        product_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate realistic property values for an event.

        Args:
            event_name: Name of the event
            event_schema: Schema definition for the event
            user_context: Current user state and context
            product_info: Product information

        Returns:
            Dictionary of property values
        """
        pass

    @abstractmethod
    def generate_user_properties(
        self,
        user_segment: str,
        product_info: Dict[str, Any],
        user_schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate initial user properties based on segment.

        Args:
            user_segment: User segment type
            product_info: Product information
            user_schema: User property schema

        Returns:
            Dictionary of initial user properties
        """
        pass

    @abstractmethod
    def generate_custom_behavior_pattern(
        self,
        product_info: Dict[str, Any],
        custom_scenario_description: str,
        event_taxonomy: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate behavior pattern for a custom scenario based on free-form text description.

        Args:
            product_info: Product/app information
            custom_scenario_description: Free-form text describing the user behavior scenario
            event_taxonomy: Event taxonomy information

        Returns:
            Behavior pattern dictionary with same structure as generate_behavior_pattern
        """
        pass

    @abstractmethod
    def analyze_property_relationships(
        self,
        taxonomy_properties: List[Dict[str, Any]],
        product_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze property relationships and determine generation rules based on taxonomy.

        Args:
            taxonomy_properties: List of property definitions from taxonomy
            product_info: Product/app information (industry, platform, description)

        Returns:
            Dictionary with:
            - property_relationships: Dependencies between properties
            - value_ranges: Realistic value ranges for each property
            - generation_strategy: How to generate each property (ai-contextual, rule-based, random-simple)
        """
        pass

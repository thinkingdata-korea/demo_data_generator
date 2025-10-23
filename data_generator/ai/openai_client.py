"""
OpenAI client for AI-powered data generation.
"""
import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI

from .base_client import BaseAIClient


class OpenAIClient(BaseAIClient):
    """OpenAI implementation of AI client"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY env var not set")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model or "gpt-4o-mini"

    def _call_api(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call OpenAI API and parse JSON response"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        content = response.choices[0].message.content
        return json.loads(content)

    def generate_behavior_pattern(
        self,
        product_info: Dict[str, Any],
        scenario: str,
        event_taxonomy: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate realistic user behavior patterns"""

        system_prompt = """You are an expert in user behavior analysis and product analytics.
Generate realistic user behavior patterns based on the product type and user scenario.
Return your response as a JSON object."""

        user_prompt = f"""Generate a realistic behavior pattern for the following context:

Product Information:
- Name: {product_info.get('product_name')}
- Industry: {product_info.get('industry')}
- Platform: {product_info.get('platform')}
- Description: {product_info.get('product_description', 'N/A')}

User Scenario: {scenario}

Available Events: {', '.join(event_taxonomy.get('events', [])[:20])}  (showing first 20)

Generate a behavior pattern with:
1. daily_session_count: How many times per day this user type typically uses the product
2. session_duration_minutes: Average session duration in minutes
3. event_frequencies: For key events, how often they occur (per session or per day)
4. event_sequences: Common user flows (sequences of events)
5. time_patterns: Activity distribution by hour (0-23), as percentages summing to 100

Return as JSON:
{{
  "daily_session_count": <number>,
  "session_duration_minutes": <number>,
  "event_frequencies": {{"event_name": <frequency>, ...}},
  "event_sequences": [["event1", "event2", ...], ...],
  "time_patterns": {{\"0\": 1.5, \"1\": 0.8, ..., \"23\": 2.1}}
}}"""

        return self._call_api(system_prompt, user_prompt)

    def generate_event_properties(
        self,
        event_name: str,
        event_schema: Dict[str, Any],
        user_context: Dict[str, Any],
        product_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate realistic property values for an event"""

        system_prompt = """You are an expert in generating realistic data for product analytics.
Generate realistic property values for an event based on the schema and context.
Return your response as a JSON object with property names as keys."""

        # Simplify schema for prompt
        properties_desc = []
        for prop in event_schema.get('properties', []):
            properties_desc.append(f"- {prop['name']} ({prop['type']}): {prop.get('description', 'N/A')}")

        user_prompt = f"""Generate realistic property values for this event:

Event: {event_name}
Description: {event_schema.get('description', 'N/A')}

Property Schema:
{chr(10).join(properties_desc)}

User Context:
{json.dumps(user_context, indent=2, ensure_ascii=False)}

Product: {product_info.get('industry')} - {product_info.get('product_name')}

Generate realistic values that make sense for this event in this context.
Return as JSON with property names as keys.
"""

        return self._call_api(system_prompt, user_prompt)

    def generate_user_properties(
        self,
        user_segment: str,
        product_info: Dict[str, Any],
        user_schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate initial user properties based on segment"""

        system_prompt = """You are an expert in user segmentation and product analytics.
Generate realistic initial user properties based on the user segment.
Return your response as a JSON object."""

        # Simplify schema for prompt
        properties_desc = []
        for prop in user_schema.get('properties', [])[:20]:  # Limit to first 20
            properties_desc.append(f"- {prop['name']} ({prop['type']}): {prop.get('description', 'N/A')}")

        user_prompt = f"""Generate initial user properties for:

User Segment: {user_segment}

Product Information:
- Industry: {product_info.get('industry')}
- Platform: {product_info.get('platform')}
- Name: {product_info.get('product_name')}

User Property Schema (first 20):
{chr(10).join(properties_desc)}

Generate realistic initial values for properties that should be set when a user first appears.
Skip properties that should remain null initially.
Return as JSON with property names as keys.
"""

        return self._call_api(system_prompt, user_prompt)

    def generate_custom_behavior_pattern(
        self,
        product_info: Dict[str, Any],
        custom_scenario_description: str,
        event_taxonomy: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate behavior pattern for a custom scenario"""

        system_prompt = """You are an expert in user behavior analysis and product analytics.
Generate realistic user behavior patterns based on custom scenario descriptions.
Analyze the scenario description and create appropriate behavior characteristics.
Return your response as a JSON object only."""

        user_prompt = f"""Generate a realistic behavior pattern for the following custom scenario:

Product Information:
- Name: {product_info.get('product_name')}
- Industry: {product_info.get('industry')}
- Platform: {product_info.get('platform')}
- Description: {product_info.get('product_description', 'N/A')}

Custom Scenario Description:
"{custom_scenario_description}"

Available Events: {', '.join(event_taxonomy.get('events', [])[:20])}  (showing first 20)

Based on this scenario description, generate appropriate behavior characteristics:

1. daily_session_count: How many times per day would this user type use the product?
2. session_duration_minutes: How long would their average session be?
3. activity_probability: What's the chance they'll be active on any given day? (0.0-1.0)
4. event_engagement: Multiplier for how many events they trigger compared to average (0.5 = half, 2.0 = double)
5. event_priorities: Which types of events would they focus on? (key: event name pattern, value: weight multiplier)
6. time_pattern: When are they most likely to be active? (morning/afternoon/evening/night/random)
7. daily_session_range: Range of sessions per day [min, max]
8. session_duration_range: Range of session duration in minutes [min, max]

Return as JSON:
{{
  "daily_session_count": <number>,
  "session_duration_minutes": <number>,
  "activity_probability": <0.0-1.0>,
  "event_engagement": <number>,
  "event_priorities": {{"pattern": <weight>, ...}},
  "time_pattern": "<morning|afternoon|evening|night|random>",
  "daily_session_range": [<min>, <max>],
  "session_duration_range": [<min>, <max>]
}}
"""

        return self._call_api(system_prompt, user_prompt)

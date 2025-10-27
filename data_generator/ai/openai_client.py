"""
OpenAI client for AI-powered data generation.
"""
import os
import json
from typing import Dict, Any, Optional, List
from openai import OpenAI

from .base_client import BaseAIClient
from ..utils.rate_limiter import RateLimiter


class OpenAIClient(BaseAIClient):
    """OpenAI implementation of AI client"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, enable_rate_limit: bool = True):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY env var not set")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model or "gpt-4o-mini"

        # Rate limiter 초기화
        self.rate_limiter = RateLimiter(max_requests=10, window_seconds=60) if enable_rate_limit else None

    def _call_api(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Call OpenAI API and parse JSON response with retry logic

        Args:
            system_prompt: System instruction
            user_prompt: User query
            max_retries: Maximum number of retry attempts for JSON parsing failures

        Returns:
            Parsed JSON response

        Raises:
            json.JSONDecodeError: If JSON parsing fails after all retries
        """
        last_error = None

        for attempt in range(max_retries):
            # Rate limit 체크
            if self.rate_limiter:
                self.rate_limiter.wait_if_needed('openai')

            # 재시도 시 JSON 출력 강조
            current_user_prompt = user_prompt
            if attempt > 0:
                current_user_prompt += "\n\n**CRITICAL: Your previous response had invalid JSON. Return ONLY valid JSON without any markdown formatting, explanations, or text outside the JSON object.**"

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": current_user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                )

                content = response.choices[0].message.content
                return json.loads(content)

            except json.JSONDecodeError as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"  ⚠️  JSON parsing failed (attempt {attempt + 1}/{max_retries}), retrying...")
                else:
                    print(f"  ❌ JSON parsing failed after {max_retries} attempts")
                    raise

        # Should never reach here, but just in case
        raise last_error if last_error else json.JSONDecodeError("Unknown error", "", 0)

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

Available Events: {', '.join(event_taxonomy.get('events', []))}

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
        for prop in user_schema.get('properties', []):
            properties_desc.append(f"- {prop['name']} ({prop['type']}): {prop.get('description', 'N/A')}")

        user_prompt = f"""Generate initial user properties for:

User Segment: {user_segment}

Product Information:
- Industry: {product_info.get('industry')}
- Platform: {product_info.get('platform')}
- Name: {product_info.get('product_name')}

User Property Schema:
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

Available Events: {', '.join(event_taxonomy.get('events', []))}

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

    def analyze_property_relationships(
        self,
        taxonomy_properties: List[Dict[str, Any]],
        product_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        택소노미의 속성들을 분석해서 속성 간 관계와 생성 규칙을 파악
        """
        system_prompt = """You are an expert in data modeling and product analytics.
Analyze the property schema and determine realistic relationships and value generation rules.
Return your response as a JSON object only."""

        # 속성 정보 요약
        properties_summary = []
        for prop in taxonomy_properties:
            properties_summary.append({
                "name": prop.get("name"),
                "type": prop.get("property_type", "string"),
                "description": prop.get("description", "")
            })

        user_prompt = f"""Analyze these properties for a {product_info.get('industry')} product ({product_info.get('platform')} platform):

Properties:
{json.dumps(properties_summary, indent=2)}

Product Description: {product_info.get('product_description', 'N/A')}

**CRITICAL REQUIREMENTS:**

1. **Logical Consistency Between Properties**:
   - Identify properties that MUST be logically consistent with each other
   - Example: carrier "#carrier" (LG U+, SKT, KT) → must match "#country" (South Korea)
   - Example: carrier (Verizon, AT&T) → must match "#country" (United States)
   - Example: "#city" must be in the correct "#country"
   - These are HARD CONSTRAINTS that must never be violated

2. **Event Context Rules**:
   - Different events require different value ranges
   - Example: "tutorial" events → level should be 1-3, low XP, minimal gold
   - Example: "first_purchase" events → might grant bonus gold/gems
   - Example: "level_up" events → level increases by 1, XP resets or increases
   - Provide event-specific constraints in "event_constraints"

3. **Property Relationships**: Which properties affect each other (e.g., level → XP, attack → combat_power)

4. **Realistic Value Ranges**: Based on industry standards and user lifecycle stage

5. **String Examples**: For string properties, provide 20-50 realistic, diverse examples
   - For "name" properties: Include names from MULTIPLE countries/cultures (Korean, Japanese, American, Chinese names)
   - For "channel" properties: Include diverse marketing channels (organic, facebook_ads, google_ads, tiktok_ads, instagram, youtube, referral, etc.)
   - For game-specific strings: Provide contextually appropriate values (server_01-99, stage_1_1 format, guild names, etc.)
   - Make example_values DIVERSE and REALISTIC for international users

6. **USER SEGMENT ANALYSIS** ⭐ MOST IMPORTANT:
   Analyze EACH user segment separately and provide specific ranges, sequences, and probabilities.

   ⚠️ **CRITICAL**: You MUST include ALL SIX segments in your response. Missing any segment will cause errors.

   User Segments to analyze (ALL REQUIRED):
   - NEW_USER: Just started, onboarding phase (days 0-3)
   - ACTIVE_USER: Regular users, established routine (days 7-90)
   - POWER_USER: Heavy users, advanced features (30+ days, high engagement)
   - CHURNING_USER: Declining engagement, at-risk users
   - CHURNED_USER: Inactive or left
   - RETURNING_USER: Coming back after absence

   For EACH segment, provide:
   a) **Property Ranges**: Specific min/max/mean for numeric properties based on ACTUAL TAXONOMY
      - Use properties that EXIST in the provided taxonomy
      - Game example: level 1-5 (mean 2), gold 0-500 (mean 200) for NEW_USER
      - E-commerce example: total_purchases 0-2 (mean 0), total_spent 0-50 (mean 10) for NEW_USER
      - SaaS example: features_used 1-3 (mean 1), sessions_count 1-5 (mean 2) for NEW_USER

   b) **Event Sequence**: Typical event flow for this segment based on ACTUAL EVENTS
      - Use events that EXIST in the provided taxonomy
      - Adapt to the industry: onboarding → core actions → advanced features

   c) **Event Probabilities**: Likelihood of each event type based on ACTUAL EVENTS
      - Use events that EXIST in the provided taxonomy
      - NEW_USER: Lower engagement, more onboarding events
      - POWER_USER: Higher engagement, more advanced/conversion events

Return JSON with this structure:
{{
  "property_constraints": {{
    "carrier": {{
      "type": "mapping",
      "maps_to": "country",
      "mappings": {{
        "SKT": "South Korea",
        "KT": "South Korea",
        "LG U+": "South Korea",
        "Verizon": "United States",
        "AT&T": "United States",
        "T-Mobile": "United States"
      }}
    }},
    "city": {{
      "type": "mapping",
      "maps_to": "country",
      "mappings": {{
        "Seoul": "South Korea",
        "Busan": "South Korea",
        "San Francisco": "United States",
        "New York": "United States"
      }}
    }}
  }},
  "event_constraints": {{
    "event_name_example": {{
      "property_name": {{"min": <number>, "max": <number>}},
      "another_property": {{"change": "+N" or "formula"}},
      "context": "Explain why these constraints exist based on event semantics"
    }}
  }},
  "property_relationships": {{
    "property_name": {{
      "depends_on": ["other_property"],
      "relationship": "description",
      "formula_hint": "optional formula"
    }}
  }},
  "value_ranges": {{
    "property_name": {{
      "min": <number>,
      "max": <number>,
      "typical": <number>,
      "context": "why this range",
      "example_values": ["value1", "value2", ...]
    }}
  }},
  "segment_analysis": {{
    "NEW_USER": {{
      "property_ranges": {{
        "<actual_property_name>": {{"min": <low>, "max": <low>, "mean": <low>}},
        "session_count": {{"min": 1, "max": 5, "mean": 2}},
        "daily_session_count": {{"min": 1, "max": 3, "mean": 1}}
      }},
      "event_sequence": ["<actual_event_names_from_taxonomy>"],
      "event_probabilities": {{
        "<onboarding_event>": 0.8,
        "<conversion_event>": 0.02
      }}
    }},
    "ACTIVE_USER": {{
      "property_ranges": {{
        "<actual_property_name>": {{"min": <medium>, "max": <medium>, "mean": <medium>}},
        "session_count": {{"min": 20, "max": 100, "mean": 50}},
        "daily_session_count": {{"min": 2, "max": 5, "mean": 3}}
      }},
      "event_sequence": ["<actual_event_names_from_taxonomy>"],
      "event_probabilities": {{
        "<core_action_event>": 0.7,
        "<conversion_event>": 0.05
      }}
    }},
    "POWER_USER": {{
      "property_ranges": {{
        "<actual_property_name>": {{"min": <high>, "max": <very_high>, "mean": <high>}},
        "session_count": {{"min": 100, "max": 500, "mean": 200}},
        "daily_session_count": {{"min": 5, "max": 15, "mean": 8}}
      }},
      "event_sequence": ["<actual_event_names_from_taxonomy>"],
      "event_probabilities": {{
        "<advanced_feature_event>": 0.9,
        "<conversion_event>": 0.2
      }}
    }},
    "CHURNING_USER": {{
      "property_ranges": {{
        "<actual_property_name>": {{"min": <medium>, "max": <medium>, "mean": <medium>}},
        "session_count": {{"min": 10, "max": 80, "mean": 30}},
        "daily_session_count": {{"min": 0.5, "max": 2, "mean": 1}}
      }},
      "event_sequence": ["<actual_event_names_from_taxonomy>"],
      "event_probabilities": {{
        "<core_action_event>": 0.3,
        "<conversion_event>": 0.01
      }}
    }},
    "CHURNED_USER": {{
      "property_ranges": {{
        "<actual_property_name>": {{"min": <low>, "max": <medium>, "mean": <low>}},
        "session_count": {{"min": 5, "max": 50, "mean": 20}}
      }},
      "event_sequence": [],
      "event_probabilities": {{}}
    }},
    "RETURNING_USER": {{
      "property_ranges": {{
        "<actual_property_name>": {{"min": <medium>, "max": <high>, "mean": <medium>}},
        "session_count": {{"min": 30, "max": 200, "mean": 80}},
        "daily_session_count": {{"min": 2, "max": 6, "mean": 3}}
      }},
      "event_sequence": ["<actual_event_names_from_taxonomy>"],
      "event_probabilities": {{
        "<re_engagement_event>": 0.8,
        "<conversion_event>": 0.08
      }}
    }}
  }},
  "generation_strategy": {{
    "property_name": "rule-based" | "ai-contextual" | "random-simple"
  }}
}}

**CRITICAL: Use ONLY properties and events that EXIST in the provided taxonomy. Do NOT assume game-specific properties like 'level' or 'gold' unless they are in the taxonomy.**

**Focus on LOGICAL CONSISTENCY and SEGMENT-SPECIFIC REALISM**:
- NEW_USER: Low engagement metrics, onboarding-focused events, minimal conversions
- ACTIVE_USER: Medium engagement, regular usage patterns, moderate conversions
- POWER_USER: High engagement metrics, advanced features, high conversion rates
- CHURNING_USER: Declining engagement, fewer sessions, low conversion probability
- CHURNED_USER: Historical data only, no recent activity
- RETURNING_USER: Re-engagement patterns, catching up on updates

**Industry Adaptation**:
- Games: progression events (tutorials → core gameplay → endgame)
- E-commerce: browse → add_to_cart → purchase flow
- SaaS: onboarding → feature adoption → power usage

**Always ensure**:
- Geographic consistency (Korean carriers only in South Korea, etc.)
- Event context alignment (early events = low metrics, late events = high metrics)
- Realistic probability distributions across segments"""

        return self._call_api(system_prompt, user_prompt)

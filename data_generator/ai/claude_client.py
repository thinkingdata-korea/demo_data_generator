"""
Claude (Anthropic) client for AI-powered data generation.
"""
import os
import json
from typing import Dict, Any, Optional, List
from anthropic import Anthropic

from .base_client import BaseAIClient
from ..utils.rate_limiter import RateLimiter


class ClaudeClient(BaseAIClient):
    """Claude (Anthropic) implementation of AI client"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, enable_rate_limit: bool = True):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided and ANTHROPIC_API_KEY env var not set")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model or "claude-sonnet-4-20250514"

        # Rate limiter 초기화
        self.rate_limiter = RateLimiter(max_requests=10, window_seconds=60) if enable_rate_limit else None

    def _call_api(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Call Claude API and parse JSON response with retry logic

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
                self.rate_limiter.wait_if_needed('anthropic')

            # 재시도 시 JSON 출력 강조
            current_user_prompt = user_prompt
            if attempt > 0:
                current_user_prompt += "\n\n**CRITICAL: Your previous response had invalid JSON. Return ONLY valid JSON without any markdown formatting, explanations, or text outside the JSON object.**"

            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": current_user_prompt}
                    ],
                    temperature=0.7,
                )

                content = message.content[0].text

                # Extract JSON from response (Claude might wrap it in markdown)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                # Try to parse JSON
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
Return your response as a JSON object only, without any markdown formatting."""

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
Return your response as a JSON object with property names as keys, without markdown formatting."""

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
Return your response as a JSON object only, without markdown formatting."""

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

    def analyze_property_relationships(
        self,
        taxonomy_properties: List[Dict[str, Any]],
        product_info: Dict[str, Any],
        event_names: List[str] = None,
    ) -> Dict[str, Any]:
        """
        택소노미의 속성과 이벤트를 분석해서 관계와 생성 규칙을 파악
        """
        system_prompt = """You are an expert data analyst specializing in user behavior and product analytics.

Your task is to analyze an event taxonomy and determine:
1. **Event Structure Analysis**: Identify sequential events, funnels, and prerequisites
2. Realistic value ranges for numeric properties based on user segments
3. Logical relationships between properties
4. Event sequences and probabilities for different user segments

Return ONLY valid JSON without markdown formatting."""

        # 속성 정보 요약
        properties_summary = []
        for prop in taxonomy_properties:
            properties_summary.append({
                "name": prop.get("name"),
                "type": prop.get("property_type", "string"),
                "description": prop.get("description", "")
            })

        # 이벤트 목록 준비
        events_list = event_names[:100] if event_names else []

        user_prompt = f"""**Product Context:**
Industry: {product_info.get('industry')}
Platform: {product_info.get('platform')}
Product Name: {product_info.get('product_name')}
Description: {product_info.get('product_description', 'N/A')}

**Events from Taxonomy:**
{json.dumps(events_list, indent=2, ensure_ascii=False)}

**Properties from Taxonomy:**
{json.dumps(properties_summary, indent=2, ensure_ascii=False)}

**YOUR TASKS:**

## Task 1: Event Structure Analysis 🎯
Analyze the events and identify:
1. **Sequential Events**: Events that must occur in specific order
   - Example: tutorial_step1 → tutorial_step2 → tutorial_step3
   - Example: stage_1_1 → stage_1_2 → stage_1_3

2. **Funnels**: Conversion flows
   - Example: view_product → add_to_cart → checkout → purchase
   - Example: browse → select → configure → checkout → purchase

3. **Prerequisites**: Events that require other events first
   - Example: "pvp_match" requires "tutorial_complete"
   - Example: "advanced_feature" requires "onboarding_complete"

4. **Lifecycle Progression**: Analyze the ACTUAL events in the taxonomy and determine the natural flow for new users
   - Identify which events represent: installation, registration, onboarding, first actions, conversions
   - Determine the logical order based on event names and descriptions
   - Include ONLY events that EXIST in the provided taxonomy
   - Example output (adapt to actual taxonomy):
     * If taxonomy has: ["app_open", "user_signup", "intro_view", "intro_complete", "level_1_start"]
     * Then: app_open → user_signup → intro_view → intro_complete → level_1_start
   - DO NOT assume specific event names like "app_install" or "tutorial_step1" - analyze what's actually provided!

Return these in "event_structure" field.

## Task 2: User Segment Analysis
Analyze behavior patterns for 6 user segments.

**CRITICAL RULES:**
⚠️ Use ONLY property names and event names that EXIST in the taxonomy above
⚠️ You MUST include ALL 6 segments: NEW_USER, ACTIVE_USER, POWER_USER, CHURNING_USER, CHURNED_USER, RETURNING_USER
⚠️ Adapt your analysis to the product's industry (games vs e-commerce vs SaaS have different patterns)
⚠️ **event_sequence** must respect the sequential order identified in Task 1

**For each segment, provide:**
1. **property_ranges**: Analyze ACTUAL numeric properties from the taxonomy and provide realistic ranges
   - Look at property names and descriptions to understand what they represent
   - For counters/metrics (session_count, purchase_count, etc.): NEW_USER = low, POWER_USER = high
   - For levels/progress (level, experience, etc.): NEW_USER = beginner, POWER_USER = advanced
   - For currency/resources: Scale appropriately to segment engagement
   - DO NOT assume properties exist - only use what's in the taxonomy!

2. **event_sequence**: Typical flow of events IN CORRECT ORDER (respecting sequential events and funnels identified in Task 1)
   - For NEW_USER: Use lifecycle_progression events
   - For ACTIVE_USER: Core feature usage patterns
   - For POWER_USER: Advanced features + high-value events

3. **event_probabilities**: Likelihood (0.0-1.0) of each event occurring
   - Based on segment engagement level
   - NEW_USER: High probability for onboarding events, low for advanced
   - POWER_USER: High probability for all events including advanced

**Segment Guidelines:**
- NEW_USER: Recently joined (0-3 days ago). VARIED progression based on ACTUAL taxonomy events:
  * Analyze which events are onboarding-related (look for: install, signup, register, tutorial, intro, guide, onboarding, etc.)
  * Determine realistic progression: Day 0 users start onboarding, Day 2-3 users may complete it
  * Event sequence MUST follow the natural onboarding flow you identified in Task 1
  * Some new users (2-5%) may reach conversion events (purchase, subscribe, etc.)
  * Include progression milestones: early events → middle events → (optional) first conversion

- ACTIVE_USER: Regular users (7-90 days), medium engagement, core feature usage, moderate conversion (5-10%)
- POWER_USER: Heavy users (30+ days), high engagement, advanced features, high conversion (15-25%)
- CHURNING_USER: Declining engagement, fewer events, low conversion (1-3%)
- CHURNED_USER: Historical data only, no active events
- RETURNING_USER: Returning after absence, re-engagement events (8-12% conversion)

**Return this exact JSON structure:**
{{
  "event_structure": {{
    "sequential_events": [
      {{
        "group_name": "tutorial_steps",
        "events": ["tutorial_step1", "tutorial_step2", "tutorial_step3"],
        "description": "Must occur in this exact order"
      }}
    ],
    "funnels": [
      {{
        "funnel_name": "purchase_funnel",
        "steps": ["view_product", "add_to_cart", "checkout", "purchase"],
        "description": "E-commerce conversion funnel"
      }}
    ],
    "prerequisites": {{
      "event_name": {{
        "requires": ["prerequisite_event1", "prerequisite_event2"],
        "description": "Why this prerequisite exists"
      }}
    }},
    "lifecycle_progression": {{
      "new_user_journey": [
        "<install_or_open_event>",
        "<registration_event>",
        "<onboarding_start_event>",
        "<onboarding_step_events_in_order>",
        "<onboarding_complete_event>",
        "<first_core_action_event>",
        "<optional_conversion_event>"
      ],
      "description": "Natural onboarding flow based on ACTUAL events in taxonomy. Replace placeholders with real event names. Users may stop at any point."
    }}
  }},
  "value_ranges": {{
    "property_name": {{
      "min": <number>,
      "max": <number>,
      "typical": <number>,
      "example_values": ["val1", "val2", ...]  // for string properties
    }}
  }},
  "property_relationships": {{
    "property_name": {{
      "depends_on": ["other_property"],
      "relationship": "description"
    }}
  }},
  "segment_analysis": {{
    "NEW_USER": {{
      "property_ranges": {{
        "<actual_property_from_taxonomy>": {{"min": <low_value>, "max": <low_value>, "mean": <low_value>}},
        "// Analyze ACTUAL numeric properties in taxonomy and provide realistic ranges for new users"
      }},
      "event_sequence": [
        "// List of events in natural order for this segment",
        "// Use ONLY event names from the taxonomy",
        "// For NEW_USER: start with onboarding events from lifecycle_progression"
      ],
      "event_probabilities": {{
        "<actual_event_from_taxonomy>": "<0.0-1.0>",
        "// Probability each event occurs for this segment",
        "// Higher probability for onboarding events in NEW_USER"
      }}
    }},
    "ACTIVE_USER": {{
      "property_ranges": {{"<property>": {{"min": <medium>, "max": <medium>, "mean": <medium>}}}},
      "event_sequence": ["<core_feature_events>"],
      "event_probabilities": {{"<event>": "<probability>"}}
    }},
    "POWER_USER": {{
      "property_ranges": {{"<property>": {{"min": <high>, "max": <high>, "mean": <high>}}}},
      "event_sequence": ["<advanced_feature_events>"],
      "event_probabilities": {{"<event>": "<high_probability>"}}
    }},
    "CHURNING_USER": {{
      "property_ranges": {{"<property>": {{"min": <medium>, "max": <medium>, "mean": <medium>}}}},
      "event_sequence": ["<declining_activity_events>"],
      "event_probabilities": {{"<event>": "<low_probability>"}}
    }},
    "CHURNED_USER": {{
      "property_ranges": {{"<property>": {{"min": <low>, "max": <medium>, "mean": <low>}}}},
      "event_sequence": [],
      "event_probabilities": {{}}
    }},
    "RETURNING_USER": {{
      "property_ranges": {{"<property>": {{"min": <medium>, "max": <high>, "mean": <medium>}}}},
      "event_sequence": ["<re_engagement_events>"],
      "event_probabilities": {{"<event>": "<moderate_probability>"}}
    }}
  }},
  "generation_strategy": {{
    "property_name": "rule-based" | "ai-contextual" | "random-simple"
  }}
}}

Remember: Use ONLY properties/events from the taxonomy above. No assumptions."""

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
Return your response as a JSON object only, without any markdown formatting."""

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

Example:
If scenario is "Users who only play on weekends for long sessions":
{{
  "daily_session_count": 2,
  "session_duration_minutes": 45,
  "activity_probability": 0.28,  // ~2 days out of 7
  "event_engagement": 1.5,
  "event_priorities": {{"game": 2.0, "purchase": 1.5, "default": 1.0}},
  "time_pattern": "afternoon",
  "daily_session_range": [1, 3],
  "session_duration_range": [30, 90]
}}
"""

        return self._call_api(system_prompt, user_prompt)

"""
User generator for creating virtual users.
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from faker import Faker

from ..models.user import User, UserSegment
from ..models.taxonomy import EventTaxonomy
from ..config.config_schema import DataGeneratorConfig, ScenarioType


class UserGenerator:
    """Generates virtual users based on configuration"""

    def __init__(self, config: DataGeneratorConfig, taxonomy: EventTaxonomy):
        self.config = config
        self.taxonomy = taxonomy
        self.faker = Faker(['ko_KR'])  # Korean locale for realistic names

        if config.seed:
            random.seed(config.seed)
            Faker.seed(config.seed)

    def generate_users(self) -> List[User]:
        """Generate all users based on configuration"""
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

        # Initialize user state with realistic values
        initial_state = self._generate_initial_state(segment, days_before_start)

        user = User(
            account_id=account_id,
            distinct_id=distinct_id,
            segment=segment,
            current_state=initial_state,
            daily_session_count=characteristics["daily_session_count"],
            session_duration_minutes=characteristics["session_duration_minutes"],
            conversion_probability=characteristics["conversion_probability"],
            first_seen_time=first_seen_dt,
            last_seen_time=first_seen_dt,
            metadata={
                "days_before_start": days_before_start,
            }
        )

        return user

    def _generate_initial_state(self, segment: UserSegment, days_before_start: int) -> Dict[str, Any]:
        """Generate initial user state with realistic values based on taxonomy"""
        state = {}

        # Generate progression level (used for calculating other values)
        if segment == UserSegment.NEW_USER:
            progression_level = random.randint(1, 5)
        elif segment == UserSegment.POWER_USER:
            progression_level = random.randint(50, 150)
        elif segment == UserSegment.CHURNED_USER:
            progression_level = random.randint(10, 40)
        else:
            progression_level = random.randint(10, 60)

        # Iterate through common properties from taxonomy
        for prop in self.taxonomy.common_properties:
            prop_name = prop.name
            prop_type = prop.property_type.value

            # Generate value based on property name and type
            value = self._generate_property_value_by_name(
                prop_name,
                prop_type,
                progression_level,
                days_before_start
            )

            state[prop_name] = value

        return state

    def _generate_property_value_by_name(
        self,
        prop_name: str,
        prop_type: str,
        progression_level: int,
        days_before_start: int
    ) -> Any:
        """Generate realistic value based on property name patterns"""
        prop_lower = prop_name.lower()

        # String type properties
        if prop_type == "string":
            if "channel" in prop_lower:
                channels = ["organic", "facebook_ads", "google_ads", "apple_search_ads", "tiktok_ads", "youtube"]
                weights = [0.4, 0.2, 0.15, 0.1, 0.1, 0.05]
                return random.choices(channels, weights=weights)[0]
            elif "server" in prop_lower:
                return f"server_{random.randint(1, 10):02d}"
            elif "name" in prop_lower or "nick" in prop_lower:
                return self.faker.name()
            elif "stage" in prop_lower or "level_id" in prop_lower:
                return f"stage_{(progression_level // 5) + 1}_{random.randint(1, 10)}"
            elif "guild" in prop_lower and random.random() > 0.3:
                return f"guild_{random.randint(1, 100):03d}"
            else:
                return f"value_{random.randint(1, 100)}"

        # Number type properties
        elif prop_type == "number":
            if "level" in prop_lower:
                return progression_level
            elif "xp" in prop_lower or "exp" in prop_lower:
                return progression_level * random.randint(800, 1200)
            elif "power" in prop_lower or "combat" in prop_lower:
                return progression_level * random.randint(100, 200)
            elif "gold" in prop_lower or "coin" in prop_lower:
                return progression_level * random.randint(500, 2000)
            elif "gem" in prop_lower or "diamond" in prop_lower or "crystal" in prop_lower:
                return progression_level * random.randint(10, 50)
            elif "stamina" in prop_lower or "energy" in prop_lower:
                return random.randint(50, 100)
            elif "pvp" in prop_lower or "rank" in prop_lower or "point" in prop_lower:
                return random.randint(0, progression_level * 10)
            elif "attack" in prop_lower:
                base = progression_level * 10
                return int(base * random.uniform(0.8, 1.2))
            elif "defense" in prop_lower or "defence" in prop_lower:
                base = progression_level * 10
                return int(base * random.uniform(0.7, 1.1))
            elif "hp" in prop_lower:
                if "max" in prop_lower:
                    base = progression_level * 10
                    return int(base * random.uniform(5, 8))
                elif "current" in prop_lower:
                    # Return same as max HP initially
                    base = progression_level * 10
                    return int(base * random.uniform(5, 8))
                else:
                    return progression_level * random.randint(50, 100)
            elif "speed" in prop_lower:
                return round(random.uniform(1.0, 2.5), 2)
            elif "rate" in prop_lower:
                return round(random.uniform(0.05, 0.30), 2)
            elif "damage" in prop_lower and "critical" in prop_lower:
                return round(random.uniform(1.5, 3.0), 2)
            elif "days" in prop_lower and "install" in prop_lower:
                return days_before_start
            elif "session" in prop_lower and "count" in prop_lower:
                return random.randint(days_before_start, days_before_start * 3)
            elif "playtime" in prop_lower or "play_time" in prop_lower:
                return random.randint(days_before_start * 10, days_before_start * 60)
            else:
                return random.randint(0, progression_level * 100)

        # Boolean type
        elif prop_type == "boolean":
            return random.choice([True, False])

        # List type
        elif prop_type == "list":
            return []

        # Time type
        elif prop_type == "time":
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Object type
        elif prop_type == "object":
            return {}

        # Default
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
        """Get behavior characteristics for a segment"""
        characteristics = {
            UserSegment.NEW_USER: {
                "daily_session_count": random.randint(2, 5),
                "session_duration_minutes": random.uniform(10, 25),
                "conversion_probability": 0.02,
            },
            UserSegment.ACTIVE_USER: {
                "daily_session_count": random.randint(1, 3),
                "session_duration_minutes": random.uniform(5, 15),
                "conversion_probability": 0.05,
            },
            UserSegment.POWER_USER: {
                "daily_session_count": random.randint(5, 15),
                "session_duration_minutes": random.uniform(20, 60),
                "conversion_probability": 0.15,
            },
            UserSegment.CHURNING_USER: {
                "daily_session_count": random.randint(0, 2),
                "session_duration_minutes": random.uniform(2, 8),
                "conversion_probability": 0.01,
            },
            UserSegment.CHURNED_USER: {
                "daily_session_count": 0,
                "session_duration_minutes": random.uniform(1, 5),
                "conversion_probability": 0.001,
            },
            UserSegment.RETURNING_USER: {
                "daily_session_count": random.randint(2, 6),
                "session_duration_minutes": random.uniform(10, 30),
                "conversion_probability": 0.08,
            },
        }

        return characteristics.get(segment, characteristics[UserSegment.ACTIVE_USER])

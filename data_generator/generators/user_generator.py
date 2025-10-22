"""
User generator for creating virtual users.
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
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
            segment = self._scenario_to_segment(scenario_config.scenario_type)

            for _ in range(count):
                user = self._create_user(segment)
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

        user = User(
            account_id=account_id,
            distinct_id=distinct_id,
            segment=segment,
            current_state={},
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

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
        """Generate initial user state with realistic values"""
        # Channel distribution
        channels = ["organic", "facebook_ads", "google_ads", "apple_search_ads", "tiktok_ads", "youtube"]
        weights = [0.4, 0.2, 0.15, 0.1, 0.1, 0.05]
        channel = random.choices(channels, weights=weights)[0]

        # Server ID (simulate multiple game servers)
        server_id = f"server_{random.randint(1, 10):02d}"

        # Level based on how long user has been around
        if segment == UserSegment.NEW_USER:
            level = random.randint(1, 5)
        elif segment == UserSegment.POWER_USER:
            level = random.randint(50, 150)
        elif segment == UserSegment.CHURNED_USER:
            level = random.randint(10, 40)
        else:
            level = random.randint(10, 60)

        # Generate name
        tmp_name = self.faker.name()

        # Calculate resources based on level
        xp = level * random.randint(800, 1200)
        combat_power = level * random.randint(100, 200)
        gold = level * random.randint(500, 2000)
        gem = level * random.randint(10, 50)
        crystal = level * random.randint(5, 30)
        stamina = random.randint(50, 100)

        # Stage progression
        main_stage_id = f"stage_{(level // 5) + 1}_{random.randint(1, 10)}"

        # Stats
        base_stat = level * 10
        tmp_stat_attack = int(base_stat * random.uniform(0.8, 1.2))
        tmp_stat_defense = int(base_stat * random.uniform(0.7, 1.1))
        tmp_stat_hp_max = int(base_stat * random.uniform(5, 8))
        tmp_stat_hp_current = tmp_stat_hp_max

        return {
            "channel": channel,
            "server_id": server_id,
            "tmp_name": tmp_name,
            "tmp_level": level,
            "tmp_xp": xp,
            "tmp_combat_power": combat_power,
            "tmp_main_stage_id": main_stage_id,
            "tmp_gold": gold,
            "tmp_gem": gem,
            "tmp_crystal": crystal,
            "tmp_stamina": stamina,
            "tmp_pvp_point": random.randint(0, level * 10),
            "tmp_guild_id": f"guild_{random.randint(1, 100):03d}" if random.random() > 0.3 else None,
            "tmp_stat_attack": tmp_stat_attack,
            "tmp_stat_defense": tmp_stat_defense,
            "tmp_stat_hp_current": tmp_stat_hp_current,
            "tmp_stat_hp_max": tmp_stat_hp_max,
            "tmp_stat_attack_speed": round(random.uniform(1.0, 2.5), 2),
            "tmp_stat_movement_speed": round(random.uniform(1.0, 2.0), 2),
            "tmp_stat_critical_rate": round(random.uniform(0.05, 0.30), 2),
            "tmp_stat_critical_damage": round(random.uniform(1.5, 3.0), 2),
            "tmp_active_buff_list": [],
            "tmp_days_since_install": days_before_start,
            "tmp_session_count": random.randint(days_before_start, days_before_start * 3),
            "tmp_total_playtime_minutes": random.randint(days_before_start * 10, days_before_start * 60),
        }

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

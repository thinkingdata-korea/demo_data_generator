"""
Log generator - generates ThinkingEngine format JSON logs.
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from ..models.user import User
from ..models.event import TrackEvent, UserSetEvent, UserSetOnceEvent, UserAddEvent
from ..models.taxonomy import EventTaxonomy, UpdateMethod
from ..config.config_schema import DataGeneratorConfig
from ..generators.behavior_engine import BehaviorEngine
from ..ai.base_client import BaseAIClient


class LogGenerator:
    """Generates realistic log data in ThinkingEngine JSON format"""

    def __init__(
        self,
        config: DataGeneratorConfig,
        taxonomy: EventTaxonomy,
        behavior_engine: BehaviorEngine,
        users: List[User],
    ):
        self.config = config
        self.taxonomy = taxonomy
        self.behavior_engine = behavior_engine
        self.users = users
        self.logs: List[str] = []

    def generate(self) -> List[str]:
        """Generate all logs for the configured period"""
        print(f"Generating logs for {len(self.users)} users from {self.config.start_date} to {self.config.end_date}")

        current_date = self.config.start_date

        while current_date <= self.config.end_date:
            print(f"Generating logs for {current_date}...")
            self._generate_day_logs(current_date)
            current_date += timedelta(days=1)

        print(f"Generated {len(self.logs)} log entries")
        return self.logs

    def _generate_day_logs(self, date: datetime):
        """Generate logs for all users for a single day"""
        # Shuffle users to randomize order
        daily_users = self.users.copy()
        random.shuffle(daily_users)

        for user in daily_users:
            self._generate_user_day_logs(user, date)

    def _generate_user_day_logs(self, user: User, date: datetime):
        """Generate logs for a single user for a single day"""
        # Get behavior pattern for user's segment
        behavior_pattern = self.behavior_engine.get_behavior_pattern(user.segment.value)

        # Generate session times
        sessions = self.behavior_engine.generate_daily_sessions(
            user=user,
            date=datetime.combine(date, datetime.min.time()),
            behavior_pattern=behavior_pattern,
        )

        # Generate logs for each session
        for session_start, session_end in sessions:
            self._generate_session_logs(user, session_start, session_end, behavior_pattern)

    def _generate_session_logs(
        self,
        user: User,
        session_start: datetime,
        session_end: datetime,
        behavior_pattern: Dict[str, Any],
    ):
        """Generate logs for a single session"""
        session_duration = (session_end - session_start).total_seconds() / 60  # minutes

        # Select events for this session
        event_names = self.behavior_engine.select_events_for_session(
            user=user,
            session_duration_minutes=session_duration,
            behavior_pattern=behavior_pattern,
        )

        if not event_names:
            return

        # Distribute events across session duration
        event_times = self._distribute_event_times(session_start, session_end, len(event_names))

        # Generate each event
        for event_name, event_time in zip(event_names, event_times):
            self._generate_event_log(user, event_name, event_time)

    def _distribute_event_times(
        self,
        start: datetime,
        end: datetime,
        count: int,
    ) -> List[datetime]:
        """Distribute event times evenly across a session"""
        if count == 0:
            return []

        if count == 1:
            return [start]

        duration = (end - start).total_seconds()
        interval = duration / (count - 1) if count > 1 else 0

        times = []
        for i in range(count):
            offset = i * interval + random.uniform(-interval * 0.2, interval * 0.2)
            offset = max(0, min(offset, duration))
            times.append(start + timedelta(seconds=offset))

        return sorted(times)

    def _generate_event_log(self, user: User, event_name: str, event_time: datetime):
        """Generate a track event log"""
        # Get event schema
        event = self.taxonomy.get_event_by_name(event_name)
        if not event:
            return

        # Build properties
        properties = {}

        # Add common properties (snapshot of user state at event time)
        properties.update(self._get_common_properties(user, event_time))

        # Add event-specific properties
        if event.properties:
            event_props = self._generate_event_properties(user, event)
            properties.update(event_props)

        # Create track event
        track_event = TrackEvent(
            **{
                "#type": "track",
                "#account_id": user.account_id,
                "#distinct_id": user.distinct_id,
                "#time": self._format_time(event_time),
                "#event_name": event_name,
                "properties": properties,
            }
        )

        self.logs.append(track_event.to_json_line())

        # Generate corresponding user updates if needed
        self._generate_user_updates(user, event_name, event_time, properties)

    def _get_common_properties(self, user: User, event_time: datetime) -> Dict[str, Any]:
        """Get common event properties (user state snapshot)"""
        properties = {}

        for prop in self.taxonomy.common_properties:
            # Get current value from user state
            value = user.get_state(prop.name)

            # If not set, generate a reasonable default
            if value is None:
                value = self._generate_default_value(prop.property_type.value)

            properties[prop.name] = value

        return properties

    def _generate_event_properties(self, user: User, event) -> Dict[str, Any]:
        """Generate event-specific properties"""
        properties = {}

        for prop in event.properties:
            # Generate value based on property type
            value = self._generate_property_value(user, prop)
            properties[prop.name] = value

        return properties

    def _generate_property_value(self, user: User, prop) -> Any:
        """Generate a realistic value for a property"""
        prop_type = prop.property_type.value

        if prop_type == "string":
            return self._generate_string_value(prop.name)
        elif prop_type == "number":
            return self._generate_number_value(prop.name)
        elif prop_type == "boolean":
            return random.choice([True, False])
        elif prop_type == "time":
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif prop_type == "list":
            return [self._generate_string_value(prop.name) for _ in range(random.randint(1, 3))]
        elif prop_type == "object":
            return {f"field_{i}": self._generate_string_value(f"{prop.name}_field") for i in range(2)}
        else:
            return None

    def _generate_string_value(self, prop_name: str) -> str:
        """Generate realistic string value based on property name"""
        prop_lower = prop_name.lower()

        if "id" in prop_lower:
            return f"id_{random.randint(1000, 9999)}"
        elif "name" in prop_lower:
            return f"item_{random.randint(1, 100)}"
        elif "channel" in prop_lower:
            return random.choice(["organic", "facebook", "google", "twitter"])
        elif "server" in prop_lower:
            return f"server_{random.randint(1, 10):02d}"
        else:
            return f"value_{random.randint(1, 100)}"

    def _generate_number_value(self, prop_name: str) -> float:
        """Generate realistic number value based on property name"""
        prop_lower = prop_name.lower()

        if "level" in prop_lower:
            return random.randint(1, 100)
        elif "gold" in prop_lower or "currency" in prop_lower:
            return random.randint(100, 100000)
        elif "price" in prop_lower or "amount" in prop_lower:
            return random.randint(1000, 50000)
        elif "count" in prop_lower:
            return random.randint(1, 10)
        elif "duration" in prop_lower or "time" in prop_lower:
            return round(random.uniform(1.0, 300.0), 2)
        else:
            return random.randint(1, 1000)

    def _generate_default_value(self, prop_type: str) -> Any:
        """Generate default value for a property type"""
        if prop_type == "string":
            return "default"
        elif prop_type == "number":
            return 0
        elif prop_type == "boolean":
            return False
        elif prop_type == "time":
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif prop_type == "list":
            return []
        elif prop_type == "object":
            return {}
        else:
            return None

    def _generate_user_updates(
        self,
        user: User,
        event_name: str,
        event_time: datetime,
        event_properties: Dict[str, Any],
    ):
        """Generate user table updates based on event"""
        # For simplicity, update user state every few events
        if random.random() < 0.3:  # 30% chance to update user state
            updates = {}

            # Example: update level or currency based on events
            if "complete" in event_name.lower() or "clear" in event_name.lower():
                updates["current_level"] = user.get_state("current_level", 1) + 1

            if "purchase" in event_name.lower():
                amount = event_properties.get("price", 1000)
                updates["total_purchase_amount"] = user.get_state("total_purchase_amount", 0) + amount

            if updates:
                user_set = UserSetEvent(
                    **{
                        "#type": "user_set",
                        "#account_id": user.account_id,
                        "#distinct_id": user.distinct_id,
                        "#time": self._format_time(event_time),
                        "properties": updates,
                    }
                )
                self.logs.append(user_set.to_json_line())

                # Update user's internal state
                user.update_state(updates)

    def _format_time(self, dt: datetime) -> str:
        """Format datetime to ThinkingEngine format"""
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # yyyy-MM-dd HH:mm:ss.SSS

    def save_to_file(self, output_path: Optional[str] = None):
        """Save logs to JSONL file"""
        if output_path is None:
            output_dir = Path(self.config.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = self.config.output_filename or f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            output_path = output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            for log in self.logs:
                f.write(log + '\n')

        print(f"Logs saved to: {output_path}")
        return output_path

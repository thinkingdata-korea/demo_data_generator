"""
Time-based patterns for realistic data generation.
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict
import numpy as np


class TimePatternGenerator:
    """Generates realistic time-based patterns"""

    @staticmethod
    def get_hourly_distribution(pattern_type: str = "normal") -> Dict[int, float]:
        """
        Get hourly activity distribution (0-23 hours).
        Returns percentage for each hour (sums to 100).
        """
        distributions = {
            "normal": {
                # Normal user pattern - peaks in morning, lunch, evening
                0: 0.5, 1: 0.3, 2: 0.2, 3: 0.1, 4: 0.1, 5: 0.2,
                6: 1.0, 7: 3.0, 8: 5.5, 9: 6.0, 10: 5.5, 11: 5.0,
                12: 6.5, 13: 5.0, 14: 4.5, 15: 4.0, 16: 4.0, 17: 5.0,
                18: 7.0, 19: 8.5, 20: 9.0, 21: 8.5, 22: 6.5, 23: 3.0
            },
            "power_user": {
                # Power users - more active throughout the day
                0: 1.5, 1: 1.0, 2: 0.5, 3: 0.3, 4: 0.3, 5: 0.5,
                6: 2.0, 7: 4.0, 8: 6.0, 9: 6.5, 10: 6.0, 11: 5.5,
                12: 6.0, 13: 5.5, 14: 5.0, 15: 5.0, 16: 5.0, 17: 5.5,
                18: 6.5, 19: 7.5, 20: 8.5, 21: 8.0, 22: 6.5, 23: 4.5
            },
            "night_owl": {
                # Night owl pattern - more active at night
                0: 5.0, 1: 4.5, 2: 4.0, 3: 3.0, 4: 2.0, 5: 1.5,
                6: 1.0, 7: 1.5, 8: 2.0, 9: 2.5, 10: 3.0, 11: 3.5,
                12: 4.0, 13: 4.0, 14: 4.0, 15: 4.5, 16: 5.0, 17: 5.5,
                18: 6.5, 19: 7.5, 20: 8.5, 21: 9.0, 22: 8.5, 23: 7.0
            },
            "morning_person": {
                # Morning person - peaks early
                0: 0.5, 1: 0.2, 2: 0.1, 3: 0.1, 4: 0.2, 5: 1.0,
                6: 4.0, 7: 8.0, 8: 9.5, 9: 8.5, 10: 7.5, 11: 6.5,
                12: 6.0, 13: 5.0, 14: 4.5, 15: 4.0, 16: 4.0, 17: 4.5,
                18: 5.5, 19: 6.0, 20: 5.5, 21: 4.5, 22: 3.0, 23: 1.5
            },
        }
        return distributions.get(pattern_type, distributions["normal"])

    @staticmethod
    def get_day_of_week_distribution() -> Dict[int, float]:
        """
        Get day-of-week activity distribution (0=Monday, 6=Sunday).
        Returns multiplier for each day.
        """
        return {
            0: 0.9,   # Monday - slightly lower
            1: 1.0,   # Tuesday
            2: 1.0,   # Wednesday
            3: 1.0,   # Thursday
            4: 1.1,   # Friday - slightly higher
            5: 1.2,   # Saturday - weekend boost
            6: 1.15,  # Sunday - weekend boost
        }

    @staticmethod
    def generate_session_times(
        date: datetime,
        session_count: int,
        hourly_dist: Dict[int, float],
        session_duration_minutes: float,
    ) -> List[tuple]:
        """
        Generate realistic session start and end times for a day.

        Returns:
            List of (start_time, end_time) tuples
        """
        sessions = []

        # Convert hourly distribution to probabilities
        hours = list(range(24))
        probs = [hourly_dist.get(h, 0) for h in hours]
        probs = np.array(probs) / sum(probs)

        # Generate session start hours
        start_hours = np.random.choice(hours, size=session_count, p=probs)
        start_hours = sorted(start_hours)

        for hour in start_hours:
            # Add random minutes within the hour
            minute = random.randint(0, 59)
            second = random.randint(0, 59)

            start_time = date.replace(hour=hour, minute=minute, second=second)

            # Calculate end time with some randomness
            duration_variance = random.uniform(0.7, 1.3)  # ±30% variance
            actual_duration = session_duration_minutes * duration_variance
            end_time = start_time + timedelta(minutes=actual_duration)

            sessions.append((start_time, end_time))

        return sessions

    @staticmethod
    def should_user_be_active(
        date: datetime,
        user_segment: str,
        base_daily_probability: float = 0.8
    ) -> bool:
        """
        Determine if a user should be active on a given day.

        Args:
            date: The date to check
            user_segment: User segment type
            base_daily_probability: Base probability of being active

        Returns:
            True if user should be active
        """
        # Adjust probability based on segment
        segment_multipliers = {
            "new_user": 0.9,  # High initial engagement
            "active_user": 1.0,
            "power_user": 1.2,  # Very consistent
            "churning_user": 0.5,  # Declining engagement
            "churned_user": 0.05,  # Rarely active
            "returning_user": 0.7,
        }

        multiplier = segment_multipliers.get(user_segment, 1.0)
        probability = base_daily_probability * multiplier

        # Day of week effect
        day_multipliers = TimePatternGenerator.get_day_of_week_distribution()
        day_multiplier = day_multipliers.get(date.weekday(), 1.0)

        final_probability = min(probability * day_multiplier, 1.0)

        return random.random() < final_probability

    @staticmethod
    def add_realistic_microseconds(dt: datetime) -> datetime:
        """Add realistic microseconds to a datetime"""
        microseconds = random.randint(0, 999999)
        return dt.replace(microsecond=microseconds)

"""
User data models for log generation.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class UserSegment(str, Enum):
    """User behavior segments"""
    NEW_USER = "new_user"  # 신규 유저
    ACTIVE_USER = "active_user"  # 활성 유저
    POWER_USER = "power_user"  # 파워 유저 (고래)
    CHURNING_USER = "churning_user"  # 이탈 위험 유저
    CHURNED_USER = "churned_user"  # 이탈 유저
    RETURNING_USER = "returning_user"  # 복귀 유저


class User(BaseModel):
    """Virtual user for log generation"""
    # IDs
    account_id: Optional[str] = Field(None, description="Account ID (logged in users)")
    distinct_id: str = Field(..., description="Device/Guest ID")

    # Profile
    segment: UserSegment = Field(..., description="User behavior segment")

    # Current state (mirrors User Table)
    current_state: Dict[str, Any] = Field(default_factory=dict, description="Current user state")

    # Behavior characteristics
    daily_session_count: int = Field(default=1, description="Average sessions per day")
    session_duration_minutes: float = Field(default=10.0, description="Average session duration")
    conversion_probability: float = Field(default=0.1, description="Probability of conversion events")

    # Timestamps
    first_seen_time: datetime = Field(..., description="First time user appeared")
    last_seen_time: datetime = Field(..., description="Last active time")

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional user metadata")

    def update_state(self, properties: Dict[str, Any]) -> None:
        """Update current user state"""
        self.current_state.update(properties)

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get current state value"""
        return self.current_state.get(key, default)

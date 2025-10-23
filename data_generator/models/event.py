"""
Event log data models following ThinkingEngine JSON structure.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import json


class TrackEvent(BaseModel):
    """
    Track event - goes to Event Table
    #type: "track"
    """
    # Metadata (fields starting with #)
    type: str = Field(default="track", alias="#type", description="Always 'track' for events")
    account_id: Optional[str] = Field(None, alias="#account_id", description="User account ID")
    distinct_id: Optional[str] = Field(None, alias="#distinct_id", description="Guest/Device ID")
    time: str = Field(..., alias="#time", description="Event time (yyyy-MM-dd HH:mm:ss.SSS)")
    event_name: str = Field(..., alias="#event_name", description="Event name")

    # Properties (actual data)
    properties: Dict[str, Any] = Field(default_factory=dict, description="Event properties (common + unique)")

    class Config:
        populate_by_name = True

    def to_json_line(self) -> str:
        """Convert to single-line JSON string"""
        data = {
            "#type": self.type,
            "#time": self.time,
            "#event_name": self.event_name,
            "properties": self.properties
        }
        if self.account_id:
            data["#account_id"] = self.account_id
        if self.distinct_id:
            data["#distinct_id"] = self.distinct_id
        return json.dumps(data, ensure_ascii=False)


class UserSetEvent(BaseModel):
    """
    User set event - updates User Table (overwrite)
    #type: "user_set"
    """
    type: str = Field(default="user_set", alias="#type")
    account_id: Optional[str] = Field(None, alias="#account_id")
    distinct_id: Optional[str] = Field(None, alias="#distinct_id")
    time: str = Field(..., alias="#time")
    properties: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True

    def to_json_line(self) -> str:
        import json
        data = {
            "#type": self.type,
            "#time": self.time,
            "properties": self.properties
        }
        if self.account_id:
            data["#account_id"] = self.account_id
        if self.distinct_id:
            data["#distinct_id"] = self.distinct_id
        return json.dumps(data, ensure_ascii=False)


class UserSetOnceEvent(BaseModel):
    """
    User set once event - updates User Table (only if null)
    #type: "user_set_once"
    """
    type: str = Field(default="user_set_once", alias="#type")
    account_id: Optional[str] = Field(None, alias="#account_id")
    distinct_id: Optional[str] = Field(None, alias="#distinct_id")
    time: str = Field(..., alias="#time")
    properties: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True

    def to_json_line(self) -> str:
        import json
        data = {
            "#type": self.type,
            "#time": self.time,
            "properties": self.properties
        }
        if self.account_id:
            data["#account_id"] = self.account_id
        if self.distinct_id:
            data["#distinct_id"] = self.distinct_id
        return json.dumps(data, ensure_ascii=False)


class UserAddEvent(BaseModel):
    """
    User add event - updates User Table (numeric increment)
    #type: "user_add"
    """
    type: str = Field(default="user_add", alias="#type")
    account_id: Optional[str] = Field(None, alias="#account_id")
    distinct_id: Optional[str] = Field(None, alias="#distinct_id")
    time: str = Field(..., alias="#time")
    properties: Dict[str, float] = Field(default_factory=dict)

    class Config:
        populate_by_name = True

    def to_json_line(self) -> str:
        import json
        data = {
            "#type": self.type,
            "#time": self.time,
            "properties": self.properties
        }
        if self.account_id:
            data["#account_id"] = self.account_id
        if self.distinct_id:
            data["#distinct_id"] = self.distinct_id
        return json.dumps(data, ensure_ascii=False)


class UserAppendEvent(BaseModel):
    """
    User append event - updates User Table (append to list)
    #type: "user_append"
    """
    type: str = Field(default="user_append", alias="#type")
    account_id: Optional[str] = Field(None, alias="#account_id")
    distinct_id: Optional[str] = Field(None, alias="#distinct_id")
    time: str = Field(..., alias="#time")
    properties: Dict[str, List[str]] = Field(default_factory=dict)

    class Config:
        populate_by_name = True

    def to_json_line(self) -> str:
        import json
        data = {
            "#type": self.type,
            "#time": self.time,
            "properties": self.properties
        }
        if self.account_id:
            data["#account_id"] = self.account_id
        if self.distinct_id:
            data["#distinct_id"] = self.distinct_id
        return json.dumps(data, ensure_ascii=False)

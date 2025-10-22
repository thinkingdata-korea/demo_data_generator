"""
Event taxonomy data models based on Excel schema.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class PropertyType(str, Enum):
    """Property data types according to ThinkingEngine"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    TIME = "time"
    LIST = "list"  # Array of strings
    OBJECT = "object"  # JSON object
    OBJECT_GROUP = "object_group"  # Array of objects


class UpdateMethod(str, Enum):
    """User property update methods"""
    USER_SET = "user_set"
    USER_SET_ONCE = "user_set_once"
    USER_ADD = "user_add"
    USER_APPEND = "user_append"
    USER_UNIQ_APPEND = "user_uniq_append"
    USER_UNSET = "user_unset"
    USER_DEL = "user_del"


class AccountSystemType(str, Enum):
    """Account system types for various products"""
    SINGLE_ACCOUNT_SINGLE_PROFILE = "단일 계정 단일 프로필"
    SINGLE_ACCOUNT_MULTI_PROFILE = "단일 계정 다중 프로필"
    NO_ACCOUNT_SYSTEM = "계정 시스템 없음"


class EventProperty(BaseModel):
    """Individual event property definition"""
    name: str = Field(..., description="속성 이름 (필수)")
    alias: Optional[str] = Field(None, description="속성 별칭")
    property_type: PropertyType = Field(..., description="속성 유형 (필수)")
    description: Optional[str] = Field(None, description="속성 설명")


class Event(BaseModel):
    """Event definition with properties"""
    event_name: str = Field(..., description="이벤트 이름 (필수)")
    event_alias: Optional[str] = Field(None, description="이벤트 별칭")
    event_description: Optional[str] = Field(None, description="이벤트 설명")
    event_tag: Optional[str] = Field(None, description="이벤트 태그")
    properties: List[EventProperty] = Field(default_factory=list, description="이벤트 고유 속성들")


class CommonEventProperty(BaseModel):
    """Common property applied to all events (snapshot at event time)"""
    name: str = Field(..., description="속성 이름 (필수)")
    alias: Optional[str] = Field(None, description="속성 별칭")
    property_type: PropertyType = Field(..., description="속성 유형 (필수)")
    description: Optional[str] = Field(None, description="속성 설명")


class UserProperty(BaseModel):
    """User profile property definition"""
    name: str = Field(..., description="속성 이름 (필수)")
    alias: Optional[str] = Field(None, description="속성 별칭")
    property_type: PropertyType = Field(..., description="속성 유형 (필수)")
    update_method: UpdateMethod = Field(..., description="업데이트 방식")
    description: Optional[str] = Field(None, description="속성 설명")
    tag: Optional[str] = Field(None, description="속성 태그")


class UserIDSchema(BaseModel):
    """User ID schema definition"""
    account_system_type: Optional[AccountSystemType] = Field(None, description="계정 시스템 유형")
    property_name: str = Field(..., description="속성 이름")
    property_alias: Optional[str] = Field(None, description="속성 별칭")
    property_description: Optional[str] = Field(None, description="속성 설명")
    value_description: Optional[str] = Field(None, description="값 설명")


class EventTaxonomy(BaseModel):
    """Complete event tracking taxonomy"""
    user_id_schemas: List[UserIDSchema] = Field(default_factory=list, description="유저 ID 체계")
    events: List[Event] = Field(default_factory=list, description="이벤트 데이터")
    common_properties: List[CommonEventProperty] = Field(default_factory=list, description="공통 이벤트 속성")
    user_properties: List[UserProperty] = Field(default_factory=list, description="유저 데이터")

    def get_event_by_name(self, event_name: str) -> Optional[Event]:
        """Get event by name"""
        for event in self.events:
            if event.event_name == event_name:
                return event
        return None

    def get_all_event_names(self) -> List[str]:
        """Get all event names"""
        return [event.event_name for event in self.events]

    def get_common_property_names(self) -> List[str]:
        """Get all common property names"""
        return [prop.name for prop in self.common_properties]

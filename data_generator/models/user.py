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


class LifecycleStage(str, Enum):
    """
    유저 생명주기 단계
    앱 설치부터 활성 사용자까지의 여정을 추적
    """
    INSTALLED = "installed"                      # 앱 설치만 완료 (첫 실행 전)
    FIRST_SESSION = "first_session"              # 첫 세션 시작
    REGISTERED = "registered"                    # 계정 등록 완료
    ONBOARDING_STARTED = "onboarding_started"    # 온보딩/튜토리얼 시작
    ONBOARDING_COMPLETED = "onboarding_completed" # 온보딩/튜토리얼 완료
    ACTIVE = "active"                            # 정규 사용자 (온보딩 이후)
    ADVANCED = "advanced"                        # 고급 사용자 (높은 참여도)


class User(BaseModel):
    """Virtual user for log generation"""
    # IDs
    account_id: Optional[str] = Field(None, description="Account ID (logged in users)")
    distinct_id: str = Field(..., description="Device/Guest ID")

    # Profile
    segment: UserSegment = Field(..., description="User behavior segment")
    lifecycle_stage: LifecycleStage = Field(default=LifecycleStage.INSTALLED, description="Current lifecycle stage")

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

    def transition_to(self, new_stage: LifecycleStage, timestamp: Optional[datetime] = None) -> bool:
        """
        유저를 새로운 생명주기 단계로 전환

        Args:
            new_stage: 새로운 단계
            timestamp: 전환 시각 (선택)

        Returns:
            전환 성공 여부
        """
        # 유효한 전환인지 확인 (순서대로만 진행 가능)
        if self._is_valid_transition(self.lifecycle_stage, new_stage):
            old_stage = self.lifecycle_stage
            self.lifecycle_stage = new_stage

            # 전환 이력 기록 (metadata에 저장)
            if "lifecycle_history" not in self.metadata:
                self.metadata["lifecycle_history"] = []

            self.metadata["lifecycle_history"].append({
                "from": old_stage.value,
                "to": new_stage.value,
                "timestamp": timestamp.isoformat() if timestamp else datetime.now().isoformat()
            })

            return True
        return False

    def _is_valid_transition(self, from_stage: LifecycleStage, to_stage: LifecycleStage) -> bool:
        """
        생명주기 전환이 유효한지 확인
        일반적으로 순서대로만 진행 (역행 불가)
        """
        # 동일 단계는 허용 안함
        if from_stage == to_stage:
            return False

        # 단계 순서 정의
        stage_order = [
            LifecycleStage.INSTALLED,
            LifecycleStage.FIRST_SESSION,
            LifecycleStage.REGISTERED,
            LifecycleStage.ONBOARDING_STARTED,
            LifecycleStage.ONBOARDING_COMPLETED,
            LifecycleStage.ACTIVE,
            LifecycleStage.ADVANCED,
        ]

        try:
            from_idx = stage_order.index(from_stage)
            to_idx = stage_order.index(to_stage)

            # 앞으로만 진행 가능 (건너뛰기는 허용)
            return to_idx > from_idx
        except ValueError:
            # 순서에 없는 단계는 항상 허용
            return True

    def can_perform_event(self, event_name: str, lifecycle_rules: Optional[Dict[str, Any]] = None) -> bool:
        """
        현재 생명주기 단계에서 이 이벤트를 수행할 수 있는지 확인

        Args:
            event_name: 이벤트명
            lifecycle_rules: 생명주기별 이벤트 규칙 (선택)

        Returns:
            수행 가능 여부
        """
        if not lifecycle_rules:
            # 규칙이 없으면 모든 이벤트 허용
            return True

        # 현재 단계에서 허용된 이벤트 패턴 확인
        stage_rules = lifecycle_rules.get(self.lifecycle_stage.value, {})

        # 1. 명시적으로 허용된 이벤트 리스트
        allowed_events = stage_rules.get("allowed_events", [])
        if "*" in allowed_events:
            # 모든 이벤트 허용
            return True

        # 2. 패턴 매칭 (예: "tutorial_*")
        for pattern in allowed_events:
            if "*" in pattern:
                # 와일드카드 패턴
                prefix = pattern.replace("*", "")
                if event_name.startswith(prefix):
                    return True
            elif pattern == event_name:
                # 정확한 매치
                return True

        # 3. 금지된 이벤트 확인
        forbidden_events = stage_rules.get("forbidden_events", [])
        for pattern in forbidden_events:
            if "*" in pattern:
                prefix = pattern.replace("*", "")
                if event_name.startswith(prefix):
                    return False
            elif pattern == event_name:
                return False

        # 규칙이 있지만 매치되지 않으면 기본 허용
        return len(allowed_events) == 0

"""
생명주기별 이벤트 규칙 및 제약조건
AI가 분석 못할 경우 사용할 하드코딩된 폴백 규칙
"""
from typing import Dict, Any, List, Optional
from ..models.user import LifecycleStage


# 생명주기 단계별 허용/금지 이벤트 규칙
LIFECYCLE_EVENT_RULES: Dict[str, Dict[str, Any]] = {
    "installed": {
        "description": "앱 설치만 완료, 아직 실행 전",
        "allowed_events": [
            "ta_app_start",    # 첫 시작
            "app_install"      # 설치 이벤트
        ],
        "forbidden_events": [],
        "first_session_sequence": [
            # 첫 세션에서 발생해야 할 이벤트 시퀀스
            "ta_app_start",
            "ta_app_view",
        ],
        "transition_events": {
            # 이벤트 발생 시 자동 전환
            "ta_app_start": LifecycleStage.FIRST_SESSION.value
        }
    },
    "first_session": {
        "description": "첫 세션 진행 중",
        "allowed_events": [
            "ta_app_*",        # 앱 기본 이벤트
            "signup",          # 회원가입
            "register",
            "login",
            "onboarding_*",    # 온보딩 시작 가능
            "tutorial_*",
            "intro_*"
        ],
        "forbidden_events": [
            "advanced_*",      # 고급 기능 금지
            "expert_*",
            "endgame_*"
        ],
        "transition_events": {
            "signup": LifecycleStage.REGISTERED.value,
            "register": LifecycleStage.REGISTERED.value,
            "login": LifecycleStage.REGISTERED.value,
        }
    },
    "registered": {
        "description": "계정 등록 완료",
        "allowed_events": [
            "*"  # 모든 이벤트 허용
        ],
        "forbidden_events": [],
        "transition_events": {
            "onboarding_start": LifecycleStage.ONBOARDING_STARTED.value,
            "tutorial_start": LifecycleStage.ONBOARDING_STARTED.value,
            "tutorial_begin": LifecycleStage.ONBOARDING_STARTED.value,
        }
    },
    "onboarding_started": {
        "description": "온보딩/튜토리얼 진행 중",
        "allowed_events": [
            "onboarding_*",
            "tutorial_*",
            "intro_*",
            "guide_*",
            "ta_app_*",        # 기본 이벤트
            "beginner_*",      # 초보자 이벤트
        ],
        "forbidden_events": [
            "advanced_*",      # 고급 기능 금지
            "expert_*",
            "master_*",
            "endgame_*",
            "pvp_*",           # PvP 금지 (게임 예시)
            "raid_*",
        ],
        "property_constraints": {
            # 이 단계에서 속성 범위 제한
            "level": {"min": 1, "max": 5},
            "days_since_install": {"min": 0, "max": 3},
            "session_count": {"min": 1, "max": 5}
        },
        "transition_events": {
            "onboarding_complete": LifecycleStage.ONBOARDING_COMPLETED.value,
            "tutorial_complete": LifecycleStage.ONBOARDING_COMPLETED.value,
            "tutorial_finished": LifecycleStage.ONBOARDING_COMPLETED.value,
        }
    },
    "onboarding_completed": {
        "description": "온보딩 완료, 일반 사용 시작",
        "allowed_events": [
            "*"  # 모든 이벤트 허용
        ],
        "forbidden_events": [],
        "auto_transition": {
            # 특정 조건에서 자동 전환
            "to_stage": LifecycleStage.ACTIVE.value,
            "conditions": {
                "min_session_count": 3,
                "or": {
                    "min_days_since_install": 7
                }
            }
        }
    },
    "active": {
        "description": "정규 활성 사용자",
        "allowed_events": [
            "*"  # 모든 이벤트 허용
        ],
        "forbidden_events": [],
        "auto_transition": {
            # 고급 사용자로 전환
            "to_stage": LifecycleStage.ADVANCED.value,
            "conditions": {
                "min_session_count": 30,
                "or": {
                    "min_days_since_install": 30,
                    "min_level": 50  # 게임 예시
                }
            }
        }
    },
    "advanced": {
        "description": "고급/파워 사용자",
        "allowed_events": [
            "*"  # 모든 이벤트 허용
        ],
        "forbidden_events": []
    }
}


# 이벤트 패턴별 제약조건 (산업 무관)
EVENT_CONSTRAINTS: Dict[str, Dict[str, Any]] = {
    "onboarding": {
        "description": "온보딩/튜토리얼 관련 이벤트",
        "patterns": [
            "onboarding",
            "tutorial",
            "intro",
            "guide",
            "walkthrough",
            "ftue"  # First Time User Experience
        ],
        "property_constraints": {
            "level": {"min": 1, "max": 5},
            "experience_points": {"min": 0, "max": 500},
            "days_since_install": {"min": 0, "max": 3},
            "session_count": {"min": 1, "max": 5}
        },
        "required_lifecycle": [
            LifecycleStage.FIRST_SESSION.value,
            LifecycleStage.REGISTERED.value,
            LifecycleStage.ONBOARDING_STARTED.value
        ]
    },
    "beginner": {
        "description": "초보자 이벤트",
        "patterns": [
            "beginner",
            "starter",
            "newbie",
            "basic",
            "simple"
        ],
        "property_constraints": {
            "level": {"min": 1, "max": 10},
            "experience_points": {"min": 0, "max": 2000},
            "days_since_install": {"min": 0, "max": 14}
        },
        "required_lifecycle": [
            LifecycleStage.ONBOARDING_STARTED.value,
            LifecycleStage.ONBOARDING_COMPLETED.value,
            LifecycleStage.ACTIVE.value
        ]
    },
    "intermediate": {
        "description": "중급 이벤트",
        "patterns": [
            "intermediate",
            "normal",
            "regular",
            "standard"
        ],
        "property_constraints": {
            "level": {"min": 10, "max": 50},
            "days_since_install": {"min": 7, "max": 60}
        },
        "required_lifecycle": [
            LifecycleStage.ACTIVE.value
        ]
    },
    "advanced": {
        "description": "고급 이벤트",
        "patterns": [
            "advanced",
            "expert",
            "master",
            "elite",
            "pro",
            "endgame",
            "hardcore"
        ],
        "property_constraints": {
            "level": {"min": 30, "max": 150},
            "days_since_install": {"min": 14, "max": 365}
        },
        "required_lifecycle": [
            LifecycleStage.ACTIVE.value,
            LifecycleStage.ADVANCED.value
        ]
    },
    "social": {
        "description": "소셜 기능 이벤트",
        "patterns": [
            "social",
            "friend",
            "guild",
            "clan",
            "team",
            "party",
            "pvp",
            "multiplayer"
        ],
        "property_constraints": {
            "level": {"min": 5, "max": 150},
            "days_since_install": {"min": 1, "max": 365}
        },
        "required_lifecycle": [
            LifecycleStage.ONBOARDING_COMPLETED.value,
            LifecycleStage.ACTIVE.value,
            LifecycleStage.ADVANCED.value
        ]
    },
    "conversion": {
        "description": "결제/전환 이벤트",
        "patterns": [
            "purchase",
            "buy",
            "payment",
            "checkout",
            "subscribe",
            "upgrade"
        ],
        "property_constraints": {
            # 최소 1회 이상 세션 필요
            "session_count": {"min": 1, "max": 1000}
        },
        "required_lifecycle": [
            # 모든 단계에서 가능 (first_session 제외)
            LifecycleStage.REGISTERED.value,
            LifecycleStage.ONBOARDING_STARTED.value,
            LifecycleStage.ONBOARDING_COMPLETED.value,
            LifecycleStage.ACTIVE.value,
            LifecycleStage.ADVANCED.value
        ]
    }
}


class LifecycleRulesEngine:
    """생명주기 규칙 엔진 - AI 분석 결과 + 하드코딩 폴백"""

    def __init__(self, ai_rules: Optional[Dict[str, Any]] = None):
        """
        Args:
            ai_rules: AI가 분석한 규칙 (선택)
        """
        self.ai_rules = ai_rules or {}
        self.hardcoded_rules = LIFECYCLE_EVENT_RULES
        self.event_constraints = EVENT_CONSTRAINTS

    def get_allowed_events_for_stage(self, lifecycle_stage: LifecycleStage) -> List[str]:
        """
        특정 생명주기 단계에서 허용된 이벤트 패턴 리스트

        Returns:
            이벤트 패턴 리스트 (예: ["ta_app_*", "tutorial_*"])
        """
        # AI 규칙 우선
        if lifecycle_stage.value in self.ai_rules:
            ai_allowed = self.ai_rules[lifecycle_stage.value].get("allowed_events", [])
            if ai_allowed:
                return ai_allowed

        # 폴백: 하드코딩 규칙
        stage_rules = self.hardcoded_rules.get(lifecycle_stage.value, {})
        return stage_rules.get("allowed_events", ["*"])

    def get_forbidden_events_for_stage(self, lifecycle_stage: LifecycleStage) -> List[str]:
        """특정 생명주기 단계에서 금지된 이벤트 패턴"""
        # AI 규칙 우선
        if lifecycle_stage.value in self.ai_rules:
            ai_forbidden = self.ai_rules[lifecycle_stage.value].get("forbidden_events", [])
            if ai_forbidden:
                return ai_forbidden

        # 폴백: 하드코딩 규칙
        stage_rules = self.hardcoded_rules.get(lifecycle_stage.value, {})
        return stage_rules.get("forbidden_events", [])

    def get_transition_event(self, lifecycle_stage: LifecycleStage, event_name: str) -> Optional[str]:
        """
        이벤트 발생 시 전환할 단계

        Args:
            lifecycle_stage: 현재 단계
            event_name: 발생한 이벤트명

        Returns:
            전환할 단계 (없으면 None)
        """
        # AI 규칙 우선
        if lifecycle_stage.value in self.ai_rules:
            ai_transitions = self.ai_rules[lifecycle_stage.value].get("transition_events", {})
            if event_name in ai_transitions:
                return ai_transitions[event_name]

        # 폴백: 하드코딩 규칙
        stage_rules = self.hardcoded_rules.get(lifecycle_stage.value, {})
        transitions = stage_rules.get("transition_events", {})

        # 정확한 매칭
        if event_name in transitions:
            return transitions[event_name]

        # 패턴 매칭 (예: "tutorial_complete" → "tutorial_*")
        for pattern, target_stage in transitions.items():
            if "*" in pattern:
                prefix = pattern.replace("*", "")
                if event_name.startswith(prefix):
                    return target_stage

        return None

    def get_property_constraints_for_event(self, event_name: str) -> Dict[str, Any]:
        """
        이벤트 이름 기반 속성 제약조건

        Returns:
            속성명 → {"min": ..., "max": ...} 딕셔너리
        """
        constraints = {}

        # 이벤트 패턴별 제약조건 확인
        for constraint_key, constraint_info in self.event_constraints.items():
            patterns = constraint_info.get("patterns", [])

            # 이벤트명이 패턴에 매치되는지 확인
            for pattern in patterns:
                if pattern.lower() in event_name.lower():
                    # 매치됨! 제약조건 적용
                    prop_constraints = constraint_info.get("property_constraints", {})
                    constraints.update(prop_constraints)
                    break

        return constraints

    def is_event_allowed_in_lifecycle(self, event_name: str, lifecycle_stage: LifecycleStage) -> bool:
        """
        이 이벤트가 현재 생명주기 단계에서 허용되는지 확인

        Args:
            event_name: 이벤트명
            lifecycle_stage: 현재 생명주기 단계

        Returns:
            허용 여부
        """
        # 1. 금지 이벤트 체크
        forbidden = self.get_forbidden_events_for_stage(lifecycle_stage)
        for pattern in forbidden:
            if self._matches_pattern(event_name, pattern):
                return False

        # 2. 허용 이벤트 체크
        allowed = self.get_allowed_events_for_stage(lifecycle_stage)

        # "*" 이면 모든 이벤트 허용
        if "*" in allowed:
            return True

        # 패턴 매칭
        for pattern in allowed:
            if self._matches_pattern(event_name, pattern):
                return True

        # 3. 이벤트 제약조건 확인 (required_lifecycle)
        for constraint_info in self.event_constraints.values():
            patterns = constraint_info.get("patterns", [])

            # 이 이벤트가 특정 카테고리에 속하는지
            for pattern in patterns:
                if pattern.lower() in event_name.lower():
                    # 필수 생명주기 단계 확인
                    required_stages = constraint_info.get("required_lifecycle", [])
                    if required_stages and lifecycle_stage.value not in required_stages:
                        return False
                    break

        # 기본: 명시적 허용이 없으면 금지
        return len(allowed) == 0

    def _matches_pattern(self, event_name: str, pattern: str) -> bool:
        """와일드카드 패턴 매칭"""
        if "*" in pattern:
            prefix = pattern.replace("*", "")
            return event_name.startswith(prefix)
        else:
            return event_name == pattern

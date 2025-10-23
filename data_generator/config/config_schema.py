"""
Configuration schema for data generator.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class IndustryType(str, Enum):
    """Industry/Product types"""
    GAME_IDLE = "game_idle"  # 방치형 게임
    GAME_RPG = "game_rpg"  # RPG 게임
    GAME_PUZZLE = "game_puzzle"  # 퍼즐 게임
    GAME_CASUAL = "game_casual"  # 캐주얼 게임
    ECOMMERCE = "ecommerce"  # 전자상거래
    MEDIA_STREAMING = "media_streaming"  # 미디어 스트리밍
    SOCIAL_NETWORK = "social_network"  # 소셜 네트워크
    FINTECH = "fintech"  # 금융 서비스
    EDUCATION = "education"  # 교육
    HEALTH_FITNESS = "health_fitness"  # 건강/피트니스
    SAAS = "saas"  # SaaS 제품
    OTHER = "other"  # 기타


class PlatformType(str, Enum):
    """Platform types"""
    MOBILE_APP = "mobile_app"  # 모바일 앱
    WEB = "web"  # 웹
    DESKTOP = "desktop"  # 데스크톱
    HYBRID = "hybrid"  # 하이브리드


class ScenarioType(str, Enum):
    """User behavior scenarios"""
    NORMAL = "normal"  # 일반 유저
    NEW_USER_ONBOARDING = "new_user_onboarding"  # 신규 유저 온보딩
    POWER_USER = "power_user"  # 파워 유저 (고래)
    CHURNING_USER = "churning_user"  # 이탈 위험 유저
    CHURNED_USER = "churned_user"  # 이탈 유저
    RETURNING_USER = "returning_user"  # 복귀 유저
    CONVERTING_USER = "converting_user"  # 전환 유저 (구매, 가입 등)


class ScenarioConfig(BaseModel):
    """Configuration for a specific scenario"""
    scenario_type: ScenarioType = Field(..., description="시나리오 유형")
    percentage: float = Field(..., ge=0, le=100, description="전체 유저 중 비율 (%)")
    description: Optional[str] = Field(None, description="시나리오 설명")
    custom_behavior: Optional[str] = Field(None, description="커스텀 행동 시나리오 (자유 텍스트, AI가 해석)")

    def is_custom(self) -> bool:
        """커스텀 시나리오인지 확인"""
        return self.custom_behavior is not None and len(self.custom_behavior.strip()) > 0

    def get_scenario_key(self) -> str:
        """시나리오를 식별하는 고유 키 반환"""
        if self.is_custom():
            # 커스텀 시나리오는 custom_behavior를 키로 사용
            return f"custom_{hash(self.custom_behavior) & 0xFFFFFFFF:08x}"
        return self.scenario_type.value


class DataGeneratorConfig(BaseModel):
    """Main configuration for data generation"""

    # Taxonomy file
    taxonomy_file: str = Field(..., description="Event taxonomy file path (Excel or CSV)")

    # Product information
    product_name: str = Field(..., description="Product/App name")
    industry: IndustryType = Field(..., description="Industry/Product type")
    custom_industry: Optional[str] = Field(None, description="Custom industry type (when industry=OTHER)")
    platform: PlatformType = Field(..., description="Platform type")

    # Date range
    start_date: date = Field(..., description="Start date for data generation")
    end_date: date = Field(..., description="End date for data generation")

    # User volume
    dau: int = Field(..., gt=0, description="Daily Active Users")
    total_users: Optional[int] = Field(None, gt=0, description="Total registered users (if None, calculated from DAU)")

    # Scenarios
    scenarios: List[ScenarioConfig] = Field(
        default_factory=lambda: [
            ScenarioConfig(scenario_type=ScenarioType.NORMAL, percentage=70, description="일반 사용자"),
            ScenarioConfig(scenario_type=ScenarioType.POWER_USER, percentage=10, description="파워 사용자"),
            ScenarioConfig(scenario_type=ScenarioType.CHURNING_USER, percentage=20, description="이탈 위험 사용자"),
        ],
        description="User behavior scenarios"
    )

    # AI Configuration
    ai_provider: str = Field(default="openai", description="AI provider (openai or anthropic)")
    ai_model: Optional[str] = Field(None, description="AI model name (if None, use default)")
    ai_api_key: Optional[str] = Field(None, description="AI API key (if None, read from env)")

    # Additional context for AI
    product_description: Optional[str] = Field(None, description="앱/제품의 특성 및 비고 (AI 컨텍스트)")

    # Custom scenario description
    custom_scenario: Optional[str] = Field(None, description="커스텀 시나리오 자유 텍스트 (예: 'D1 유저들이 튜토리얼에서 많이 이탈')")

    # Data generation volume
    avg_events_per_user_per_day: Optional[tuple] = Field(
        default=(5, 30),
        description="1인당 하루 평균 이벤트 발생량 범위 (min, max)"
    )

    # Output configuration
    output_dir: str = Field(default="./data_generator/output", description="Output directory")
    output_filename: Optional[str] = Field(None, description="Output filename (if None, auto-generated)")

    # Advanced options
    timezone: str = Field(default="Asia/Seoul", description="Timezone for timestamps")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")

    @field_validator("scenarios")
    @classmethod
    def validate_scenario_percentages(cls, scenarios: List[ScenarioConfig]) -> List[ScenarioConfig]:
        """Validate that scenario percentages sum to 100"""
        total = sum(s.percentage for s in scenarios)
        if not (99.9 <= total <= 100.1):  # Allow for floating point errors
            raise ValueError(f"Scenario percentages must sum to 100, got {total}")
        return scenarios

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, end_date: date, info) -> date:
        """Validate that end_date is after start_date"""
        if "start_date" in info.data and end_date < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return end_date

    def get_date_range_days(self) -> int:
        """Get number of days in date range"""
        return (self.end_date - self.start_date).days + 1

    def get_total_users_estimate(self) -> int:
        """Estimate total users based on DAU"""
        if self.total_users:
            return self.total_users
        # Simple heuristic: total users ~ DAU * 3-5
        return int(self.dau * 3.5)

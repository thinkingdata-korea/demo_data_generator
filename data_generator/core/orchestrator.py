"""
Core orchestrator for data generation workflow.
전체 데이터 생성 프로세스를 조율하는 핵심 모듈
"""
from typing import List, Dict, Any
from pathlib import Path

from ..config.config_schema import DataGeneratorConfig
from ..models.taxonomy import EventTaxonomy
from ..models.user import User
from ..readers.taxonomy_reader import TaxonomyReader
from ..generators.user_generator import UserGenerator
from ..generators.behavior_engine import BehaviorEngine
from ..generators.log_generator import LogGenerator
from ..ai.openai_client import OpenAIClient
from ..ai.claude_client import ClaudeClient
from ..ai.base_client import BaseAIClient


class DataGenerationOrchestrator:
    """전체 데이터 생성 프로세스를 조율하는 오케스트레이터"""

    def __init__(self, config: DataGeneratorConfig):
        self.config = config
        self.taxonomy: EventTaxonomy = None
        self.ai_client: BaseAIClient = None
        self.users: List[User] = None
        self.behavior_engine: BehaviorEngine = None
        self.log_generator: LogGenerator = None

    def execute(self) -> Dict[str, Any]:
        """
        전체 데이터 생성 프로세스 실행

        Returns:
            결과 정보 딕셔너리
        """
        # 1. 택소노미 로드
        self.taxonomy = self._load_taxonomy()

        # 2. AI 클라이언트 초기화
        self.ai_client = self._initialize_ai_client()

        # 3. 유저 생성
        self.users = self._generate_users()

        # 4. 행동 엔진 초기화
        self.behavior_engine = self._initialize_behavior_engine()

        # 5. 로그 생성
        logs = self._generate_logs()

        # 6. 파일 저장
        output_path = self._save_logs(logs)

        return {
            "success": True,
            "taxonomy": {
                "events": len(self.taxonomy.events),
                "common_properties": len(self.taxonomy.common_properties),
                "user_properties": len(self.taxonomy.user_properties),
            },
            "users": len(self.users),
            "logs": len(logs),
            "output_path": str(output_path),
        }

    def _load_taxonomy(self) -> EventTaxonomy:
        """택소노미 파일 로드"""
        reader = TaxonomyReader(self.config.taxonomy_file)
        return reader.read()

    def _initialize_ai_client(self) -> BaseAIClient:
        """AI 클라이언트 초기화"""
        if self.config.ai_provider == "openai":
            return OpenAIClient(
                api_key=self.config.ai_api_key,
                model=self.config.ai_model
            )
        else:
            return ClaudeClient(
                api_key=self.config.ai_api_key,
                model=self.config.ai_model
            )

    def _generate_users(self) -> List[User]:
        """가상 유저 생성"""
        user_gen = UserGenerator(self.config, self.taxonomy)
        return user_gen.generate_users()

    def _initialize_behavior_engine(self) -> BehaviorEngine:
        """행동 패턴 엔진 초기화"""
        # industry 표시: custom_industry가 있으면 사용, 없으면 기본 값
        industry_display = self.config.custom_industry if self.config.custom_industry else self.config.industry.value

        product_info = {
            "product_name": self.config.product_name,
            "industry": industry_display,
            "platform": self.config.platform.value,
            "product_description": self.config.product_description,
            "custom_scenario": self.config.custom_scenario,
        }

        # 커스텀 시나리오 수집
        custom_scenarios = {}
        for scenario_config in self.config.scenarios:
            if scenario_config.is_custom():
                scenario_key = scenario_config.get_scenario_key()
                custom_scenarios[scenario_key] = scenario_config.custom_behavior

        return BehaviorEngine(self.ai_client, self.taxonomy, product_info, custom_scenarios)

    def _generate_logs(self) -> List[str]:
        """로그 데이터 생성"""
        self.log_generator = LogGenerator(
            self.config,
            self.taxonomy,
            self.behavior_engine,
            self.users
        )
        return self.log_generator.generate()

    def _save_logs(self, logs: List[str]) -> Path:
        """로그를 파일로 저장"""
        return self.log_generator.save_to_file()

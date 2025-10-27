"""
Log generator - generates ThinkingEngine format JSON logs.
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from ..models.user import User, LifecycleStage
from ..models.event import TrackEvent, UserSetEvent, UserSetOnceEvent, UserAddEvent
from ..models.taxonomy import EventTaxonomy, UpdateMethod
from ..config.config_schema import DataGeneratorConfig
from ..generators.behavior_engine import BehaviorEngine
from ..generators.preset_properties import PresetPropertiesGenerator
from ..generators.intelligent_property_generator import IntelligentPropertyGenerator
from ..generators.property_update_engine import PropertyUpdateEngine
from ..ai.base_client import BaseAIClient
from ..utils.property_validator import PropertyNameValidator


class LogGenerator:
    """Generates realistic log data in ThinkingEngine JSON format"""

    def __init__(
        self,
        config: DataGeneratorConfig,
        taxonomy: EventTaxonomy,
        behavior_engine: BehaviorEngine,
        users: List[User],
        ai_client: Optional[BaseAIClient] = None,
        intelligent_generator: Optional[IntelligentPropertyGenerator] = None,
    ):
        self.config = config
        self.taxonomy = taxonomy
        self.behavior_engine = behavior_engine
        self.users = users
        self.logs: List[str] = []

        # 유저별 캐싱
        self.user_preset_cache: Dict[str, Dict[str, Any]] = {}
        self.user_set_generated: set = set()  # 이미 user_set 생성된 유저 추적

        # 프리셋 속성 생성기는 나중에 초기화 (intelligent_generator 필요)
        self.preset_generator = None

        # 제품 정보 (AI 생성기들에서 공통 사용)
        self.product_info = {
            "industry": config.industry,
            "platform": config.platform,
            "product_name": config.product_name,
            "product_description": config.product_description or ""
        }

        # AI 기반 지능형 속성 생성기 (외부에서 전달받거나 직접 생성)
        self.intelligent_generator: Optional[IntelligentPropertyGenerator] = intelligent_generator
        self.update_engine: Optional[PropertyUpdateEngine] = None
        self._intelligent_generator_needs_analysis = False  # 분석이 필요한지 추적

        # intelligent_generator가 외부에서 전달되지 않았고 ai_client가 있으면 직접 생성 (레거시 지원)
        if not self.intelligent_generator and ai_client:
            # 택소노미에서 모든 속성 수집
            all_properties = []
            all_properties.extend(taxonomy.common_properties)
            for event in taxonomy.events:
                if event.properties:
                    all_properties.extend(event.properties)

            # 지능형 속성 생성기
            self.intelligent_generator = IntelligentPropertyGenerator(
                ai_client=ai_client,
                taxonomy_properties=all_properties,
                product_info=self.product_info
            )
            self._intelligent_generator_needs_analysis = True  # 방금 생성했으므로 분석 필요

        # 속성 업데이트 엔진 초기화 (ai_client 있을 때만)
        if ai_client:
            self.update_engine = PropertyUpdateEngine(
                ai_client=ai_client,
                taxonomy=taxonomy,
                product_info=self.product_info
            )

        # 생성된 파일 경로 리스트
        self.generated_files: List[Path] = []

    def generate(self) -> List[str]:
        """
        Generate all logs for the configured period (daily file split mode)
        각 날짜별로 파일을 생성하고 바로 저장
        """
        total_days = (self.config.end_date - self.config.start_date).days + 1
        print(f"Generating logs for {len(self.users)} users from {self.config.start_date} to {self.config.end_date} ({total_days} days)")

        # AI 기반 분석 수행 (필요한 경우에만)
        # orchestrator에서 이미 분석된 인스턴스를 받았으면 스킵
        if self.intelligent_generator and self._intelligent_generator_needs_analysis:
            print("  🤖 로그 속성 생성을 위한 AI 분석 중...")
            self.intelligent_generator.analyze_properties()

        if self.update_engine:
            self.update_engine.analyze_event_update_patterns()

        # 프리셋 속성 생성기 초기화 (intelligent_generator 전달)
        if not self.preset_generator:
            self.preset_generator = PresetPropertiesGenerator(
                platform=self.config.platform,
                product_name=self.config.product_name,
                intelligent_generator=self.intelligent_generator
            )

        # 출력 디렉토리 생성
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        current_date = self.config.start_date
        day_count = 0

        while current_date <= self.config.end_date:
            day_count += 1
            print(f"\n[{day_count}/{total_days}] Generating logs for {current_date}...")

            # 해당 날짜의 로그 생성
            self.logs = []  # 메모리 초기화
            self._generate_day_logs(current_date)

            # 즉시 파일로 저장
            if self.logs:
                daily_file = self._save_daily_logs(current_date)
                self.generated_files.append(daily_file)
                print(f"  ✓ Saved {len(self.logs):,} logs to {daily_file.name}")
            else:
                print(f"  ⚠ No logs generated for {current_date}")

            current_date += timedelta(days=1)

        total_logs = sum(self._count_lines_in_file(f) for f in self.generated_files)
        print(f"\n✓ Generation complete!")
        print(f"  Total days: {len(self.generated_files)}")
        print(f"  Total logs: {total_logs:,}")
        print(f"  Files: {output_dir}")

        # 마지막 날짜의 로그를 반환 (하위 호환성)
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
        # Get behavior pattern - use scenario_key if available, otherwise use segment
        scenario_key = user.metadata.get("scenario_key", user.segment.value)
        behavior_pattern = self.behavior_engine.get_behavior_pattern(scenario_key)

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

        # 세션 컨텍스트 준비 (이벤트별 전용 속성에 사용)
        session_context = {
            "session_start": session_start,
            "session_duration": int((session_end - session_start).total_seconds()),
            "is_resume": random.random() < 0.3,  # 30% 확률로 백그라운드에서 재시작
            "background_duration": random.randint(10, 300),
        }

        # 세션 이벤트 시퀀스 추적 (이벤트 컨텍스트 기반 속성 생성에 활용)
        session_events = []

        # Generate each event
        for event_name, event_time in zip(event_names, event_times):
            self._generate_event_log(user, event_name, event_time, session_context, session_events)
            session_events.append(event_name)

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

    def _generate_initial_user_set(self, user: User, event_time: datetime):
        """
        Generate initial user_set event with USER properties
        Called on user's first event to set all user properties from taxonomy
        """
        # Get user_properties from user metadata (generated by user_generator)
        user_props = user.metadata.get("user_properties", {})

        if not user_props:
            return

        # preset properties를 context로 준비
        preset_props = self._get_user_preset_properties(user)
        additional_context = preset_props.copy()

        # For None values, try to generate using intelligent_generator
        final_props = {}
        for prop_name, value in user_props.items():
            if value is None and self.intelligent_generator:
                # Find property type from taxonomy
                for prop in self.taxonomy.user_properties:
                    if prop.name == prop_name:
                        value = self.intelligent_generator.generate_property_value(
                            prop_name=prop_name,
                            prop_type=prop.property_type.value,
                            user=user,
                            event_name=None,
                            session_events=None,
                            additional_context=additional_context
                        )
                        break

            # None이 아닌 값만 추가
            if value is not None:
                final_props[prop_name] = value

        # 설정할 속성이 없으면 생성하지 않음
        if not final_props:
            return

        # Sanitize property names
        final_props = PropertyNameValidator.sanitize_properties(final_props)

        # Create user_set event
        user_set = UserSetEvent(
            **{
                "#type": "user_set",
                "#account_id": user.account_id,
                "#distinct_id": user.distinct_id,
                "#time": self._format_time(event_time),
                "properties": final_props,
            }
        )
        self.logs.append(user_set.to_json_line())

        # Update user's internal state
        user.update_state(final_props)

    def _generate_event_log(self, user: User, event_name: str, event_time: datetime, session_context: Optional[Dict[str, Any]] = None, session_events: Optional[List[str]] = None):
        """Generate a track event log"""
        # 첫 이벤트 발생 시 USER properties를 user_set으로 설정
        user_key = user.account_id or user.distinct_id
        if user_key not in self.user_set_generated:
            self._generate_initial_user_set(user, event_time)
            self.user_set_generated.add(user_key)

        # Get event schema
        event = self.taxonomy.get_event_by_name(event_name)
        if not event:
            return

        # Build properties
        properties = {}

        # 1. Add preset properties (플랫폼별 필수 프리셋 속성)
        preset_props = self._get_user_preset_properties(user)
        properties.update(preset_props)

        # 2. Add common properties (snapshot of user state at event time)
        properties.update(self._get_common_properties(user, event_time))

        # 3. Add event-specific properties (택소노미 정의)
        if event.properties:
            event_props = self._generate_event_properties(user, event, session_events)
            properties.update(event_props)

        # 4. Add event-specific preset properties (이벤트별 전용 속성: ta_app_start, ta_app_end 등)
        event_preset_props = self.preset_generator.generate_event_specific_properties(
            event_name=event_name,
            session_context=session_context
        )
        properties.update(event_preset_props)

        # Validate and sanitize property names
        properties = PropertyNameValidator.sanitize_properties(properties)

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

        # 생명주기 단계 전환 확인 (이벤트 기반)
        self._check_lifecycle_transition(user, event_name, event_time)

    def _get_user_preset_properties(self, user: User) -> Dict[str, Any]:
        """
        유저별 프리셋 속성 반환 (캐싱 사용)
        디바이스 ID, OS 등은 유저별로 일관되어야 하므로 캐싱
        """
        user_key = user.account_id or user.distinct_id

        if user_key not in self.user_preset_cache:
            # 처음 생성 - 유저의 가입일을 install_date로 사용
            install_date = user.metadata.get("created_at")
            preset_props = self.preset_generator.generate(
                user_id=user_key,
                install_date=install_date
            )
            self.user_preset_cache[user_key] = preset_props

        return self.user_preset_cache[user_key].copy()

    def _get_common_properties(self, user: User, event_time: datetime) -> Dict[str, Any]:
        """Get common event properties (user state snapshot)"""
        properties = {}

        # preset properties를 context로 준비 (국가, 디바이스 정보 등)
        preset_props = self._get_user_preset_properties(user)
        additional_context = preset_props.copy()

        for prop in self.taxonomy.common_properties:
            # Get current value from user state
            value = user.get_state(prop.name)

            # If not set, generate a value
            if value is None:
                # name 같은 중요한 속성은 intelligent generator 사용
                if "name" in prop.name.lower() and self.intelligent_generator:
                    value = self.intelligent_generator.generate_property_value(
                        prop_name=prop.name,
                        prop_type=prop.property_type.value,
                        user=user,
                        event_name=None,
                        session_events=None,
                        additional_context=additional_context
                    )
                else:
                    # 기타 속성은 기본값 사용
                    value = self._generate_default_value(prop.property_type.value)

            properties[prop.name] = value

        return properties

    def _generate_event_properties(self, user: User, event, session_events: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate event-specific properties"""
        properties = {}

        for prop in event.properties:
            # Generate value based on property type
            value = self._generate_property_value(user, prop, event.event_name, session_events)
            properties[prop.name] = value

        return properties

    def _generate_property_value(self, user: User, prop, event_name: Optional[str] = None, session_events: Optional[List[str]] = None) -> Any:
        """Generate a realistic value for a property"""
        prop_type = prop.property_type.value

        # AI 기반 생성기가 있으면 사용
        if self.intelligent_generator:
            # preset properties를 context로 전달
            preset_props = self._get_user_preset_properties(user)
            additional_context = preset_props.copy()

            return self.intelligent_generator.generate_property_value(
                prop_name=prop.name,
                prop_type=prop_type,
                user=user,
                event_name=event_name,
                session_events=session_events,
                additional_context=additional_context
            )

        # 폴백: 기본 랜덤 생성 (AI 없을 때만)
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
        """Generate string value (폴백 - AI 없을 때만)"""
        # 범용적인 포맷 사용
        return f"{prop_name}_{random.randint(1, 1000)}"

    def _generate_number_value(self, prop_name: str) -> float:
        """Generate number value (폴백 - AI 없을 때만)"""
        # 범용적인 범위 사용
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
        """Generate user table updates based on event (AI 기반 범용 업데이트 엔진 사용)"""
        updates = {}

        # 1. AI 기반 업데이트 엔진 우선 사용 (범용, 산업 무관)
        if self.update_engine:
            ai_updates = self.update_engine.get_updates_for_event(
                event_name=event_name,
                user=user,
                event_properties=event_properties
            )
            updates.update(ai_updates)

        # 2. 폴백: 회원가입/로그인 이벤트에 대한 기본 처리
        if not updates:
            event_lower = event_name.lower()
            if any(keyword in event_lower for keyword in ["signup", "register", "login", "start"]):
                # name이 없으면 이벤트 속성에서 가져오거나 생성
                for prop_name in self.taxonomy.common_properties:
                    if "name" in prop_name.name.lower() and user.get_state(prop_name.name) is None:
                        # 이벤트 속성에 이미 있으면 사용
                        if prop_name.name in event_properties:
                            updates[prop_name.name] = event_properties[prop_name.name]

        # 3. 추가 폴백: intelligent_generator의 관계 기반 업데이트 (확률적)
        if random.random() < 0.2 and self.intelligent_generator:
            fallback_updates = self.intelligent_generator.should_update_user_property(
                event_name=event_name,
                user=user,
                event_properties=event_properties
            )
            # 기존 updates와 충돌하지 않는 것만 추가
            for key, value in fallback_updates.items():
                if key not in updates:
                    updates[key] = value

        # updates가 있으면 user_set 이벤트 생성
        if updates:
            # Validate and sanitize property names
            updates = PropertyNameValidator.sanitize_properties(updates)

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

    def _save_daily_logs(self, date: datetime) -> Path:
        """
        일일 로그를 파일로 저장

        Args:
            date: 날짜

        Returns:
            저장된 파일 경로
        """
        output_dir = Path(self.config.output_dir)
        filename = f"logs_{date.strftime('%Y%m%d')}.jsonl"
        output_path = output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            for log in self.logs:
                f.write(log + '\n')

        return output_path

    def _count_lines_in_file(self, file_path: Path) -> int:
        """파일의 라인 수 카운트"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except:
            return 0

    def save_to_file(self, output_path: Optional[str] = None) -> Path:
        """
        Save logs to JSONL file (legacy method for backward compatibility)

        Note: In daily split mode, this returns the path to the output directory
        """
        if self.generated_files:
            # 일일 분할 모드: 출력 디렉토리 반환
            return Path(self.config.output_dir)
        else:
            # 단일 파일 모드 (하위 호환성)
            if output_path is None:
                output_dir = Path(self.config.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)

                filename = self.config.output_filename or f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
                output_path = output_dir / filename

            with open(output_path, 'w', encoding='utf-8') as f:
                for log in self.logs:
                    f.write(log + '\n')

            print(f"Logs saved to: {output_path}")
            return Path(output_path)

    def get_generated_files(self) -> List[Path]:
        """생성된 파일 목록 반환"""
        return self.generated_files.copy()

    def _check_lifecycle_transition(self, user: User, event_name: str, event_time: datetime):
        """
        이벤트 발생 후 생명주기 단계 전환 확인

        Args:
            user: 유저 객체
            event_name: 발생한 이벤트명
            event_time: 이벤트 시각
        """
        if not hasattr(self.behavior_engine, 'lifecycle_rules'):
            return

        # 이벤트에 따른 전환 확인
        lifecycle_rules = self.behavior_engine.lifecycle_rules
        target_stage = lifecycle_rules.get_transition_event(user.lifecycle_stage, event_name)

        if target_stage:
            # LifecycleStage enum으로 변환
            try:
                new_stage = LifecycleStage(target_stage)
                success = user.transition_to(new_stage, event_time)

                if success:
                    # 전환 성공 시 로그 (디버깅용)
                    # print(f"  Lifecycle transition: {user.distinct_id} -> {new_stage.value}")
                    pass
            except ValueError:
                # 잘못된 단계명
                pass

"""
설정 관리자 - 사용자 설정을 저장하고 불러옵니다.
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.prompt import Prompt

console = Console()


class SettingsManager:
    """사용자 설정 관리"""

    def __init__(self, config_file: str = ".demo_data_generator_config.json"):
        """
        Args:
            config_file: 설정 파일 경로 (프로젝트 루트 기준)
        """
        self.config_file = Path.home() / config_file  # 홈 디렉토리에 저장
        self.settings: Dict[str, Any] = {}
        self.load()

    def load(self):
        """설정 파일에서 설정을 불러옵니다."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            except Exception as e:
                console.print(f"[yellow]⚠️  설정 파일 로드 실패: {e}[/yellow]")
                self.settings = {}
        else:
            self.settings = {}

    def save(self):
        """현재 설정을 파일에 저장합니다."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            console.print(f"[dim]✓ 설정 저장됨: {self.config_file}[/dim]")
        except Exception as e:
            console.print(f"[yellow]⚠️  설정 파일 저장 실패: {e}[/yellow]")

    def get(self, key: str, default: Any = None) -> Any:
        """설정 값을 가져옵니다."""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """설정 값을 저장합니다."""
        self.settings[key] = value

    def prompt_and_save(
        self,
        key: str,
        prompt_text: str,
        default: Optional[str] = None,
        password: bool = False,
        required: bool = True
    ) -> Optional[str]:
        """
        설정 값을 프롬프트로 입력받고 저장합니다.
        이미 설정이 있으면 기존 값을 사용할지 물어봅니다.

        Args:
            key: 설정 키
            prompt_text: 사용자에게 표시할 프롬프트 텍스트
            default: 기본값
            password: 비밀번호 입력 여부 (마스킹)
            required: 필수 입력 여부

        Returns:
            입력된 값 또는 기존 설정 값
        """
        existing_value = self.get(key)

        # 기존 설정이 있는 경우
        if existing_value:
            # 비밀번호는 마스킹해서 표시
            display_value = "****" + existing_value[-4:] if password and len(existing_value) > 4 else existing_value

            use_existing = Prompt.ask(
                f"  {prompt_text}\n  [dim]기존 설정: {display_value}[/dim]\n  기존 설정을 사용하시겠습니까? (y/n)",
                choices=["y", "n"],
                default="y"
            )

            if use_existing == "y":
                return existing_value

        # 새로 입력받기
        if password:
            value = Prompt.ask(f"  {prompt_text}", password=True, default=default or "")
        else:
            value = Prompt.ask(f"  {prompt_text}", default=default or "")

        # 필수 입력인데 비어있으면 다시 입력
        if required and not value:
            console.print("[yellow]  ⚠️  필수 입력 항목입니다.[/yellow]")
            return self.prompt_and_save(key, prompt_text, default, password, required)

        # 저장
        if value:
            self.set(key, value)
            self.save()

        return value if value else None

    def get_openai_api_key(self) -> Optional[str]:
        """OpenAI API 키를 가져옵니다."""
        return self.prompt_and_save(
            "openai_api_key",
            "OpenAI API Key를 입력하세요",
            password=True,
            required=False
        )

    def get_anthropic_api_key(self) -> Optional[str]:
        """Anthropic API 키를 가져옵니다."""
        return self.prompt_and_save(
            "anthropic_api_key",
            "Anthropic API Key를 입력하세요",
            password=True,
            required=False
        )

    def get_te_app_id(self) -> Optional[str]:
        """ThinkingEngine APP ID를 가져옵니다."""
        return self.prompt_and_save(
            "te_app_id",
            "ThinkingEngine APP ID를 입력하세요",
            required=False
        )

    def get_te_receiver_url(self) -> Optional[str]:
        """ThinkingEngine Receiver URL을 가져옵니다."""
        return self.prompt_and_save(
            "te_receiver_url",
            "ThinkingEngine Receiver URL을 입력하세요",
            default="https://te-receiver-naver.thinkingdata.kr/",
            required=False
        )

    def get_logbus_path(self) -> Optional[str]:
        """LogBus2 바이너리 경로를 가져옵니다."""
        return self.prompt_and_save(
            "logbus_path",
            "LogBus2 바이너리 경로를 입력하세요",
            default="./logbus 2/logbus",
            required=False
        )

    def clear(self):
        """모든 설정을 삭제합니다."""
        self.settings = {}
        if self.config_file.exists():
            self.config_file.unlink()
        console.print("[green]✓ 모든 설정이 삭제되었습니다.[/green]")

    def show(self):
        """현재 설정을 표시합니다."""
        if not self.settings:
            console.print("[yellow]저장된 설정이 없습니다.[/yellow]")
            return

        console.print("\n[bold cyan]현재 저장된 설정:[/bold cyan]")
        for key, value in self.settings.items():
            # 비밀번호/키는 마스킹
            if "key" in key.lower() or "password" in key.lower():
                display_value = "****" + value[-4:] if len(value) > 4 else "****"
            else:
                display_value = value
            console.print(f"  • {key}: {display_value}")
        console.print()

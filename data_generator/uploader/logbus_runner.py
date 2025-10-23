"""
LogBus2 실행 및 관리 모듈
"""
import os
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel

from .logbus_config import LogBusConfig

console = Console()


class LogBusRunner:
    """LogBus2 실행 및 관리"""

    def __init__(self, logbus_bin_path: str, working_dir: Optional[str] = None):
        """
        Args:
            logbus_bin_path: LogBus2 바이너리 경로 (예: "./logbus 2/logbus")
            working_dir: LogBus2 실행 디렉터리 (None이면 logbus_bin_path의 부모 디렉터리)
        """
        self.logbus_bin = Path(logbus_bin_path).absolute()
        if not self.logbus_bin.exists():
            raise FileNotFoundError(f"LogBus2 바이너리를 찾을 수 없습니다: {self.logbus_bin}")

        if working_dir:
            self.working_dir = Path(working_dir).absolute()
        else:
            self.working_dir = self.logbus_bin.parent

        self.conf_dir = self.working_dir / "conf"
        self.conf_file = self.conf_dir / "daemon.json"

    def _run_command(self, command: str, check: bool = True) -> subprocess.CompletedProcess:
        """LogBus2 명령 실행"""
        # Use list format to properly handle paths with spaces
        cmd_list = [str(self.logbus_bin), command]
        return subprocess.run(
            cmd_list,
            cwd=str(self.working_dir),
            capture_output=True,
            text=True,
            check=check
        )

    def setup_config(self, config: LogBusConfig) -> Path:
        """
        설정 파일 생성

        Args:
            config: LogBusConfig 객체

        Returns:
            생성된 설정 파일 경로
        """
        self.conf_dir.mkdir(parents=True, exist_ok=True)
        return config.save(self.conf_file)

    def validate_config(self) -> bool:
        """설정 파일 검증"""
        if not self.conf_file.exists():
            console.print(f"[red]✗ 설정 파일이 없습니다: {self.conf_file}[/red]")
            return False

        try:
            result = self._run_command("env", check=False)
            if result.returncode == 0:
                console.print("[green]✓ 설정 파일 검증 완료[/green]")
                return True
            else:
                console.print(f"[red]✗ 설정 파일 검증 실패[/red]")
                console.print(result.stderr)
                return False
        except Exception as e:
            console.print(f"[red]✗ 설정 검증 중 오류: {str(e)}[/red]")
            return False

    def start(self) -> bool:
        """LogBus2 시작"""
        try:
            console.print("[cyan]LogBus2 시작 중...[/cyan]")
            result = self._run_command("start")

            if result.returncode == 0:
                console.print("[green]✓ LogBus2가 시작되었습니다[/green]")
                console.print(result.stdout)
                return True
            else:
                console.print("[red]✗ LogBus2 시작 실패[/red]")
                console.print(result.stderr)
                return False
        except Exception as e:
            console.print(f"[red]✗ LogBus2 시작 중 오류: {str(e)}[/red]")
            return False

    def stop(self) -> bool:
        """LogBus2 중지"""
        try:
            console.print("[cyan]LogBus2 중지 중...[/cyan]")
            result = self._run_command("stop", check=False)

            if result.returncode == 0:
                console.print("[green]✓ LogBus2가 중지되었습니다[/green]")
                return True
            else:
                console.print("[yellow]⚠ LogBus2가 실행 중이 아닙니다[/yellow]")
                return False
        except Exception as e:
            console.print(f"[red]✗ LogBus2 중지 중 오류: {str(e)}[/red]")
            return False

    def restart(self) -> bool:
        """LogBus2 재시작"""
        try:
            console.print("[cyan]LogBus2 재시작 중...[/cyan]")
            result = self._run_command("restart")

            if result.returncode == 0:
                console.print("[green]✓ LogBus2가 재시작되었습니다[/green]")
                return True
            else:
                console.print("[red]✗ LogBus2 재시작 실패[/red]")
                console.print(result.stderr)
                return False
        except Exception as e:
            console.print(f"[red]✗ LogBus2 재시작 중 오류: {str(e)}[/red]")
            return False

    def status(self) -> Dict[str, Any]:
        """LogBus2 상태 확인"""
        try:
            result = self._run_command("env", check=False)
            return {
                "running": result.returncode == 0,
                "output": result.stdout if result.returncode == 0 else result.stderr
            }
        except Exception as e:
            return {
                "running": False,
                "output": str(e)
            }

    def progress(self) -> Optional[str]:
        """전송 진행 상태 확인"""
        try:
            result = self._run_command("progress", check=False)
            if result.returncode == 0:
                return result.stdout
            else:
                return None
        except Exception as e:
            console.print(f"[red]✗ 진행 상태 확인 중 오류: {str(e)}[/red]")
            return None

    def reset(self) -> bool:
        """LogBus 읽기 기록 초기화"""
        try:
            console.print("[yellow]⚠ LogBus2 읽기 기록을 초기화합니다...[/yellow]")
            result = self._run_command("reset", check=False)

            if result.returncode == 0:
                console.print("[green]✓ 읽기 기록이 초기화되었습니다[/green]")
                return True
            else:
                console.print("[red]✗ 읽기 기록 초기화 실패[/red]")
                console.print(result.stderr)
                return False
        except Exception as e:
            console.print(f"[red]✗ 읽기 기록 초기화 중 오류: {str(e)}[/red]")
            return False

    def upload_and_monitor(
        self,
        config: LogBusConfig,
        monitor_interval: int = 5,
        auto_stop: bool = True
    ) -> bool:
        """
        데이터 업로드 및 모니터링

        Args:
            config: LogBusConfig 객체
            monitor_interval: 모니터링 간격 (초)
            auto_stop: 업로드 완료 후 자동 중지 여부

        Returns:
            성공 여부
        """
        # 1. 설정 파일 생성
        console.print("[cyan]1. 설정 파일 생성 중...[/cyan]")
        self.setup_config(config)
        console.print(f"[green]✓ 설정 파일 생성: {self.conf_file}[/green]")

        # 2. 설정 검증
        console.print("\n[cyan]2. 설정 검증 중...[/cyan]")
        if not self.validate_config():
            return False

        # 3. LogBus2 시작
        console.print("\n[cyan]3. LogBus2 시작...[/cyan]")
        if not self.start():
            return False

        # 4. 진행 상태 모니터링
        console.print(f"\n[cyan]4. 업로드 진행 상태 모니터링 (간격: {monitor_interval}초)[/cyan]")
        console.print("[dim]Ctrl+C를 눌러 모니터링을 중단할 수 있습니다[/dim]\n")

        try:
            last_progress = None
            while True:
                time.sleep(monitor_interval)

                # 진행 상태 확인
                progress = self.progress()
                if progress and progress != last_progress:
                    console.print(progress)
                    last_progress = progress

                    # 완료 여부 확인 (간단한 구현)
                    # 실제로는 더 정교한 로직이 필요할 수 있음
                    if "100%" in progress or "완료" in progress:
                        console.print("\n[green]✓ 업로드 완료![/green]")
                        break

        except KeyboardInterrupt:
            console.print("\n[yellow]모니터링이 중단되었습니다[/yellow]")

        # 5. 자동 중지
        if auto_stop:
            console.print("\n[cyan]5. LogBus2 중지...[/cyan]")
            self.stop()

        console.print("\n[bold green]✓ 업로드 프로세스 완료[/bold green]")
        return True

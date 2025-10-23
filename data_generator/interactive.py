"""
Interactive CLI for data generator.
"""
from datetime import date
from pathlib import Path
from typing import Optional, Dict, Any
import click
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config.config_schema import DataGeneratorConfig, IndustryType, PlatformType
from .config.settings_manager import SettingsManager
from .readers.taxonomy_reader import TaxonomyReader
from .core.orchestrator import DataGenerationOrchestrator

console = Console()


def validate_date(date_str: str) -> bool:
    """Validate date format YYYY-MM-DD"""
    try:
        date.fromisoformat(date_str)
        return True
    except:
        return False


def interactive_mode():
    """Run data generator in interactive mode"""

    console.print("\n[bold cyan]🎮 Demo Data Generator - 대화형 모드[/bold cyan]")
    console.print("=" * 70)
    console.print()

    # 설정 관리자 초기화
    settings = SettingsManager()

    try:
        # 1. Taxonomy file
        console.print("[bold yellow]📁 Step 1: 택소노미 파일[/bold yellow]")
        taxonomy_path = Prompt.ask(
            "  택소노미 파일 경로를 입력하세요",
            default="event_tracking/data/예시 - 방치형 게임.xlsx"
        )

        if not Path(taxonomy_path).exists():
            console.print(f"[red]✗ 파일을 찾을 수 없습니다: {taxonomy_path}[/red]")
            return

        # Load taxonomy
        reader = TaxonomyReader(taxonomy_path)
        taxonomy = reader.read()
        console.print(f"[green]✓ 택소노미 로드 완료[/green]")
        console.print(f"  - 이벤트: {len(taxonomy.events)}개")
        console.print(f"  - 공통 속성: {len(taxonomy.common_properties)}개")
        console.print(f"  - 유저 속성: {len(taxonomy.user_properties)}개")
        console.print()

        # 2. Product info
        console.print("[bold yellow]📱 Step 2: 제품 정보[/bold yellow]")
        product_name = Prompt.ask("  제품/앱 이름", default="My Product")

        console.print("\n  산업 유형 선택:")
        industries = [
            "game_idle", "game_rpg", "game_puzzle", "game_casual",
            "ecommerce", "media_streaming", "social_network",
            "fintech", "education", "health_fitness", "saas", "other"
        ]
        for i, ind in enumerate(industries, 1):
            console.print(f"    {i}. {ind}")

        industry_idx = IntPrompt.ask("  선택 (번호)", default=1) - 1
        industry = industries[industry_idx] if 0 <= industry_idx < len(industries) else industries[0]

        # If 'other' is selected, ask for custom industry
        custom_industry = None
        if industry == "other":
            custom_industry = Prompt.ask("  커스텀 산업 유형을 입력하세요 (예: healthcare, automotive, logistics)")
            console.print(f"  [green]✓ 커스텀 산업 유형: {custom_industry}[/green]")

        console.print("\n  플랫폼 유형:")
        platforms = ["mobile_app", "web", "desktop", "hybrid"]
        for i, plat in enumerate(platforms, 1):
            console.print(f"    {i}. {plat}")

        platform_idx = IntPrompt.ask("  선택 (번호)", default=1) - 1
        platform = platforms[platform_idx] if 0 <= platform_idx < len(platforms) else platforms[0]
        console.print()

        # 3. Date range
        console.print("[bold yellow]📊 Step 3: 데이터 생성 기간[/bold yellow]")
        while True:
            start_date_str = Prompt.ask("  시작 날짜 (YYYY-MM-DD)", default="2024-01-01")
            if validate_date(start_date_str):
                start_date = date.fromisoformat(start_date_str)
                break
            console.print("  [red]올바른 날짜 형식이 아닙니다 (YYYY-MM-DD)[/red]")

        while True:
            end_date_str = Prompt.ask("  종료 날짜 (YYYY-MM-DD)", default="2024-01-07")
            if validate_date(end_date_str):
                end_date = date.fromisoformat(end_date_str)
                if end_date >= start_date:
                    break
                console.print("  [red]종료 날짜는 시작 날짜보다 늦어야 합니다[/red]")
            else:
                console.print("  [red]올바른 날짜 형식이 아닙니다 (YYYY-MM-DD)[/red]")

        days = (end_date - start_date).days + 1
        console.print(f"[dim]  → 총 {days}일간의 데이터 생성[/dim]")
        console.print()

        # 4. DAU
        console.print("[bold yellow]👥 Step 4: 사용자 수[/bold yellow]")
        dau = IntPrompt.ask("  DAU (일일 활성 사용자)", default=100)
        estimated_total = int(dau * 3.5)
        console.print(f"[dim]  → 예상 전체 유저 수: {estimated_total:,}명[/dim]")
        console.print()

        # 5. Product description
        console.print("[bold yellow]📝 Step 5: 제품 특성 및 비고 (선택사항)[/bold yellow]")
        console.print("[dim]  제품의 특성, 주요 기능, 타겟 유저 등을 자유롭게 입력하세요.[/dim]")
        console.print("[dim]  AI가 이 정보를 참고하여 더 현실적인 데이터를 생성합니다.[/dim]")
        description = Prompt.ask("  입력", default="")
        console.print()

        # 6. Custom scenario
        console.print("[bold yellow]🎯 Step 6: 커스텀 시나리오 (선택사항)[/bold yellow]")
        console.print("[dim]  특정 상황을 시뮬레이션하고 싶다면 자유롭게 입력하세요.[/dim]")
        console.print("[dim]  예: 'D1 유저의 30%가 튜토리얼에서 이탈', '주말에 활동량 2배 증가' 등[/dim]")
        custom_scenario = Prompt.ask("  입력", default="")
        console.print()

        # 7. Event volume
        console.print("[bold yellow]📈 Step 7: 이벤트 발생량[/bold yellow]")
        avg_events_min = IntPrompt.ask("  1인당 하루 평균 최소 이벤트 수", default=5)
        avg_events_max = IntPrompt.ask("  1인당 하루 평균 최대 이벤트 수", default=30)
        console.print()

        # 8. AI provider and API key
        console.print("[bold yellow]🤖 Step 8: AI 제공자 및 API 키[/bold yellow]")
        console.print("  1. OpenAI (GPT)")
        console.print("  2. Anthropic (Claude)")
        ai_choice = IntPrompt.ask("  선택 (번호)", default=2)
        ai_provider = "anthropic" if ai_choice == 2 else "openai"

        # API 키 입력 (설정에서 불러오거나 새로 입력)
        console.print()
        if ai_provider == "anthropic":
            api_key = settings.get_anthropic_api_key()
        else:
            api_key = settings.get_openai_api_key()

        if not api_key:
            console.print("[yellow]  ⚠️  API 키가 필요합니다. 계속 진행하려면 API 키를 입력하세요.[/yellow]")
            return

        console.print()

        # 9. Output
        console.print("[bold yellow]💾 Step 9: 출력 설정[/bold yellow]")
        output_dir = Prompt.ask("  출력 디렉토리", default="./data_generator/output")
        console.print()

        # Summary
        console.print("=" * 70)
        industry_display = f"{industry} ({custom_industry})" if custom_industry else industry
        console.print(Panel.fit(
            f"""[bold]설정 확인[/bold]

[cyan]제품 정보[/cyan]
  • 이름: {product_name}
  • 산업: {industry_display}
  • 플랫폼: {platform}

[cyan]데이터 생성[/cyan]
  • 기간: {start_date} ~ {end_date} ({days}일)
  • DAU: {dau:,}명
  • 예상 전체 유저: {estimated_total:,}명
  • 평균 이벤트: {avg_events_min}~{avg_events_max}개/일

[cyan]AI 설정[/cyan]
  • 제공자: {ai_provider}
  • 제품 특성: {description or '(없음)'}
  • 커스텀 시나리오: {custom_scenario or '(없음)'}

[cyan]출력[/cyan]
  • 디렉토리: {output_dir}
""",
            title="📋 최종 확인",
            border_style="cyan"
        ))
        console.print()

        if not Confirm.ask("이대로 진행하시겠습니까?", default=True):
            console.print("[yellow]취소되었습니다.[/yellow]")
            return

        # Create config
        config = DataGeneratorConfig(
            taxonomy_file=taxonomy_path,
            product_name=product_name,
            industry=IndustryType(industry),
            custom_industry=custom_industry,
            platform=PlatformType(platform),
            start_date=start_date,
            end_date=end_date,
            dau=dau,
            total_users=None,
            ai_provider=ai_provider,
            ai_model=None,
            product_description=description if description else None,
            custom_scenario=custom_scenario if custom_scenario else None,
            avg_events_per_user_per_day=(avg_events_min, avg_events_max),
            output_dir=output_dir,
            seed=None,
        )

        # Generate data using orchestrator
        console.print("\n[bold cyan]⚙️  데이터 생성 시작...[/bold cyan]")
        console.print()

        orchestrator = DataGenerationOrchestrator(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            task = progress.add_task("[cyan]택소노미 로드 중...", total=None)
            orchestrator.taxonomy = orchestrator._load_taxonomy()
            progress.update(task, completed=True, description=f"[green]✓ 택소노미 로드 완료")

            task = progress.add_task("[cyan]AI 클라이언트 초기화 중...", total=None)
            orchestrator.ai_client = orchestrator._initialize_ai_client()
            progress.update(task, completed=True, description=f"[green]✓ AI 클라이언트 준비 완료")

            task = progress.add_task("[cyan]가상 유저 생성 중...", total=None)
            orchestrator.users = orchestrator._generate_users()
            progress.update(task, completed=True, description=f"[green]✓ {len(orchestrator.users):,}명의 유저 생성 완료")

            task = progress.add_task("[cyan]행동 패턴 엔진 초기화 중...", total=None)
            orchestrator.behavior_engine = orchestrator._initialize_behavior_engine()
            progress.update(task, completed=True, description=f"[green]✓ 행동 패턴 엔진 준비 완료")

            task = progress.add_task("[cyan]로그 데이터 생성 중 (일일 파일 분할)...", total=None)
            result = orchestrator.execute()
            progress.update(task, completed=True, description=f"[green]✓ 로그 생성 완료")

        console.print()

        # 생성된 파일 정보
        generated_files = orchestrator.log_generator.get_generated_files() if orchestrator.log_generator else []
        total_logs = result.get("logs", 0)
        output_dir = result.get("output_path", "")

        console.print(Panel.fit(
            f"""[bold green]✓ 데이터 생성 완료![/bold green]

[cyan]생성 결과[/cyan]
  • 총 일수: [bold]{len(generated_files)}[/bold]일
  • 총 로그 수: [bold]{total_logs:,}[/bold]개
  • 출력 디렉토리: [bold]{output_dir}[/bold]
  • 파일 개수: [bold]{len(generated_files)}[/bold]개

[cyan]생성된 파일 (일일 분할)[/cyan]
  {chr(10).join([f'  • {f.name}' for f in generated_files[:5]])}
  {'  • ... 외 ' + str(len(generated_files) - 5) + '개' if len(generated_files) > 5 else ''}

[cyan]다음 단계[/cyan]
  1. 생성된 JSON 파일들을 확인하세요
  2. upload 명령어로 디렉토리를 업로드하세요:
     python -m data_generator.main upload -d {output_dir}
  3. 필요시 다른 설정으로 다시 생성하세요
""",
            title="🎉 완료",
            border_style="green"
        ))

    except KeyboardInterrupt:
        console.print("\n[yellow]사용자에 의해 중단되었습니다.[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]✗ 오류 발생: {str(e)}[/bold red]")
        raise

"""
Main entry point for data generator.
"""
import os
from datetime import date
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

from .config.config_schema import DataGeneratorConfig, IndustryType, PlatformType, ScenarioType, ScenarioConfig
from .readers.taxonomy_reader import TaxonomyReader
from .generators.user_generator import UserGenerator
from .generators.behavior_engine import BehaviorEngine
from .generators.log_generator import LogGenerator
from .ai.openai_client import OpenAIClient
from .ai.claude_client import ClaudeClient
from .interactive import interactive_mode
from .uploader.logbus_config import LogBusConfigGenerator
from .uploader.logbus_runner import LogBusRunner

# Load environment variables
load_dotenv()

console = Console()


@click.group()
def cli():
    """Demo Data Generator - 현실적인 로그 데이터 생성기"""
    pass


@cli.command()
def interactive():
    """대화형 모드로 데이터 생성 (추천)"""
    interactive_mode()


@cli.command()
@click.option('--taxonomy', '-t', required=True, type=click.Path(exists=True), help='택소노미 Excel/CSV 파일 경로')
@click.option('--product-name', '-p', required=True, help='제품/앱 이름')
@click.option('--industry', '-i', required=True, type=click.Choice([e.value for e in IndustryType]), help='산업 유형')
@click.option('--platform', required=True, type=click.Choice([e.value for e in PlatformType]), help='플랫폼 유형')
@click.option('--start-date', required=True, type=click.DateTime(formats=['%Y-%m-%d']), help='시작 날짜 (YYYY-MM-DD)')
@click.option('--end-date', required=True, type=click.DateTime(formats=['%Y-%m-%d']), help='종료 날짜 (YYYY-MM-DD)')
@click.option('--dau', required=True, type=int, help='일일 활성 사용자 수 (DAU)')
@click.option('--total-users', type=int, default=None, help='전체 등록 유저 수 (기본값: DAU * 3.5)')
@click.option('--ai-provider', type=click.Choice(['openai', 'anthropic']), default='openai', help='AI 제공자')
@click.option('--ai-model', type=str, default=None, help='AI 모델 이름 (선택)')
@click.option('--description', type=str, default=None, help='앱/제품 특성 및 비고 (AI 컨텍스트)')
@click.option('--custom-scenario', type=str, default=None, help='커스텀 시나리오 (예: "D1 유저가 튜토리얼에서 많이 이탈")')
@click.option('--avg-events-min', type=int, default=5, help='1인당 하루 평균 최소 이벤트 수')
@click.option('--avg-events-max', type=int, default=30, help='1인당 하루 평균 최대 이벤트 수')
@click.option('--output-dir', '-o', type=click.Path(), default='./data_generator/output', help='출력 디렉토리')
@click.option('--seed', type=int, default=None, help='재현성을 위한 랜덤 시드')
def generate(
    taxonomy: str,
    product_name: str,
    industry: str,
    platform: str,
    start_date,
    end_date,
    dau: int,
    total_users: Optional[int],
    ai_provider: str,
    ai_model: Optional[str],
    description: Optional[str],
    custom_scenario: Optional[str],
    avg_events_min: int,
    avg_events_max: int,
    output_dir: str,
    seed: Optional[int],
):
    """Generate log data based on taxonomy and configuration"""

    console.print("\n[bold cyan]Demo Data Generator[/bold cyan]")
    console.print("=" * 60)

    # Create config
    config = DataGeneratorConfig(
        taxonomy_file=taxonomy,
        product_name=product_name,
        industry=IndustryType(industry),
        platform=PlatformType(platform),
        start_date=start_date.date(),
        end_date=end_date.date(),
        dau=dau,
        total_users=total_users,
        ai_provider=ai_provider,
        ai_model=ai_model,
        product_description=description,
        custom_scenario=custom_scenario,
        avg_events_per_user_per_day=(avg_events_min, avg_events_max),
        output_dir=output_dir,
        seed=seed,
    )

    console.print(f"\n[green]Configuration:[/green]")
    console.print(f"  Product: {config.product_name}")
    console.print(f"  Industry: {config.industry.value}")
    console.print(f"  Platform: {config.platform.value}")
    console.print(f"  Date Range: {config.start_date} to {config.end_date} ({config.get_date_range_days()} days)")
    console.print(f"  DAU: {config.dau:,}")
    console.print(f"  Total Users: {config.get_total_users_estimate():,}")
    console.print(f"  AI Provider: {config.ai_provider}")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Step 1: Load taxonomy
            task = progress.add_task("[cyan]Loading taxonomy...", total=None)
            reader = TaxonomyReader(taxonomy)
            taxonomy_data = reader.read()
            progress.update(task, completed=True, description=f"[green]✓ Loaded taxonomy ({len(taxonomy_data.events)} events)")

            # Step 2: Initialize AI client
            task = progress.add_task(f"[cyan]Initializing AI client ({ai_provider})...", total=None)
            if ai_provider == 'openai':
                ai_client = OpenAIClient(model=ai_model)
            else:
                ai_client = ClaudeClient(model=ai_model)
            progress.update(task, completed=True, description=f"[green]✓ AI client ready")

            # Step 3: Generate users
            task = progress.add_task("[cyan]Generating users...", total=None)
            user_gen = UserGenerator(config, taxonomy_data)
            users = user_gen.generate_users()
            progress.update(task, completed=True, description=f"[green]✓ Generated {len(users):,} users")

            # Step 4: Initialize behavior engine
            task = progress.add_task("[cyan]Initializing behavior engine...", total=None)
            product_info = {
                "product_name": config.product_name,
                "industry": config.industry.value,
                "platform": config.platform.value,
                "product_description": config.product_description,
            }
            behavior_engine = BehaviorEngine(ai_client, taxonomy_data, product_info)
            progress.update(task, completed=True, description=f"[green]✓ Behavior engine ready")

            # Step 5: Generate logs
            task = progress.add_task("[cyan]Generating logs...", total=None)
            log_gen = LogGenerator(config, taxonomy_data, behavior_engine, users)
            logs = log_gen.generate()
            progress.update(task, completed=True, description=f"[green]✓ Generated {len(logs):,} log entries")

            # Step 6: Save to file
            task = progress.add_task("[cyan]Saving to file...", total=None)
            output_path = log_gen.save_to_file()
            progress.update(task, completed=True, description=f"[green]✓ Saved to {output_path}")

        console.print(f"\n[bold green]✓ Generation complete![/bold green]")
        console.print(f"Output file: [cyan]{output_path}[/cyan]")
        console.print(f"Total logs: [cyan]{len(logs):,}[/cyan]")

    except Exception as e:
        console.print(f"\n[bold red]✗ Error: {str(e)}[/bold red]")
        raise


@cli.command()
@click.argument('taxonomy_file', type=click.Path(exists=True))
def inspect(taxonomy_file: str):
    """Inspect a taxonomy file"""
    console.print(f"\n[bold cyan]Inspecting taxonomy: {taxonomy_file}[/bold cyan]")
    console.print("=" * 60)

    try:
        reader = TaxonomyReader(taxonomy_file)
        taxonomy = reader.read()

        console.print(f"\n[green]Events:[/green] {len(taxonomy.events)}")
        for i, event in enumerate(taxonomy.events[:10], 1):
            console.print(f"  {i}. {event.event_name} ({len(event.properties)} properties)")
        if len(taxonomy.events) > 10:
            console.print(f"  ... and {len(taxonomy.events) - 10} more")

        console.print(f"\n[green]Common Properties:[/green] {len(taxonomy.common_properties)}")
        for prop in taxonomy.common_properties[:10]:
            console.print(f"  - {prop.name} ({prop.property_type.value})")

        console.print(f"\n[green]User Properties:[/green] {len(taxonomy.user_properties)}")
        for prop in taxonomy.user_properties[:10]:
            console.print(f"  - {prop.name} ({prop.property_type.value}, {prop.update_method.value})")

        console.print(f"\n[green]User ID Schemas:[/green] {len(taxonomy.user_id_schemas)}")
        for schema in taxonomy.user_id_schemas:
            console.print(f"  - {schema.property_name}")

    except Exception as e:
        console.print(f"\n[bold red]✗ Error: {str(e)}[/bold red]")
        raise


@cli.command()
@click.option('--data-file', '-f', required=True, type=click.Path(exists=True), help='업로드할 데이터 파일 경로 (.jsonl)')
@click.option('--app-id', '-a', required=True, help='ThinkingEngine APP ID')
@click.option('--push-url', '-u', required=True, help='ThinkingEngine Receiver URL')
@click.option('--logbus-path', '-l', default='./logbus 2/logbus', type=click.Path(exists=True), help='LogBus2 바이너리 경로')
@click.option('--cpu-limit', type=int, default=4, help='CPU 코어 수 제한')
@click.option('--compress', is_flag=True, default=True, help='Gzip 압축 사용')
@click.option('--auto-remove', is_flag=True, default=False, help='업로드 후 파일 자동 삭제')
@click.option('--remove-after-days', type=int, default=7, help='파일 삭제 기간 (일)')
@click.option('--monitor-interval', type=int, default=5, help='모니터링 간격 (초)')
@click.option('--no-auto-stop', is_flag=True, default=False, help='업로드 후 LogBus 자동 중지 안 함')
def upload(
    data_file: str,
    app_id: str,
    push_url: str,
    logbus_path: str,
    cpu_limit: int,
    compress: bool,
    auto_remove: bool,
    remove_after_days: int,
    monitor_interval: int,
    no_auto_stop: bool,
):
    """생성된 데이터를 ThinkingEngine으로 업로드"""
    console.print("\n[bold cyan]📤 LogBus2 데이터 업로드[/bold cyan]")
    console.print("=" * 60)

    console.print(f"\n[green]설정:[/green]")
    console.print(f"  데이터 파일: {data_file}")
    console.print(f"  APP ID: {app_id}")
    console.print(f"  Receiver URL: {push_url}")
    console.print(f"  LogBus2 경로: {logbus_path}")
    console.print(f"  압축: {'사용' if compress else '미사용'}")
    console.print(f"  자동 삭제: {'사용' if auto_remove else '미사용'}")
    if auto_remove:
        console.print(f"  삭제 기간: {remove_after_days}일")
    console.print()

    try:
        # 1. LogBus2 설정 생성
        config = LogBusConfigGenerator.create_config(
            data_file_path=data_file,
            app_id=app_id,
            push_url=push_url,
            cpu_limit=cpu_limit,
            http_compress="gzip" if compress else "none",
            auto_remove=auto_remove,
            remove_after_days=remove_after_days
        )

        # 2. LogBus2 실행
        runner = LogBusRunner(logbus_path)

        # 3. 업로드 및 모니터링
        success = runner.upload_and_monitor(
            config=config,
            monitor_interval=monitor_interval,
            auto_stop=not no_auto_stop
        )

        if success:
            console.print("\n[bold green]✓ 업로드 완료![/bold green]")
        else:
            console.print("\n[bold red]✗ 업로드 실패[/bold red]")

    except Exception as e:
        console.print(f"\n[bold red]✗ 오류: {str(e)}[/bold red]")
        raise


if __name__ == '__main__':
    cli()

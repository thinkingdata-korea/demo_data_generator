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

# Load environment variables
load_dotenv()

console = Console()


@click.group()
def cli():
    """Demo Data Generator - Generate realistic log data for analytics"""
    pass


@cli.command()
@click.option('--taxonomy', '-t', required=True, type=click.Path(exists=True), help='Path to taxonomy Excel/CSV file')
@click.option('--product-name', '-p', required=True, help='Product/App name')
@click.option('--industry', '-i', required=True, type=click.Choice([e.value for e in IndustryType]), help='Industry type')
@click.option('--platform', required=True, type=click.Choice([e.value for e in PlatformType]), help='Platform type')
@click.option('--start-date', required=True, type=click.DateTime(formats=['%Y-%m-%d']), help='Start date (YYYY-MM-DD)')
@click.option('--end-date', required=True, type=click.DateTime(formats=['%Y-%m-%d']), help='End date (YYYY-MM-DD)')
@click.option('--dau', required=True, type=int, help='Daily Active Users')
@click.option('--total-users', type=int, default=None, help='Total registered users (default: DAU * 3.5)')
@click.option('--ai-provider', type=click.Choice(['openai', 'anthropic']), default='openai', help='AI provider')
@click.option('--ai-model', type=str, default=None, help='AI model name (optional)')
@click.option('--description', type=str, default=None, help='Product description for AI context')
@click.option('--output-dir', '-o', type=click.Path(), default='./data_generator/output', help='Output directory')
@click.option('--seed', type=int, default=None, help='Random seed for reproducibility')
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


if __name__ == '__main__':
    cli()

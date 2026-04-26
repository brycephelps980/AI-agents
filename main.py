#!/usr/bin/env python3
"""
AI-Agents — entry point.

Usage:
  python main.py daemon                    Start the scheduler daemon (runs overnight)
  python main.py run-now                   Run the full pipeline immediately
  python main.py run-tier <past|present|future>   Run one tier only
  python main.py run-agent <agent_name>    Run a single agent in isolation
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Ensure project root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
from utils.config import load_config
from rich.console import Console

console = Console()
setup_logger()


def _check_api_key() -> None:
    cfg = load_config()
    if not cfg.anthropic_api_key:
        console.print("[bold red]Error:[/] ANTHROPIC_API_KEY is not set.")
        console.print("Copy .env.example → .env and add your key, or set the env var directly.")
        sys.exit(1)


def cmd_daemon(args) -> None:
    _check_api_key()
    from orchestrator.orchestrator import RootOrchestrator
    from scheduler.scheduler import SchedulerService
    orchestrator = RootOrchestrator()
    svc = SchedulerService(orchestrator)
    console.print("[bold green]AI-Agents daemon starting...[/]")
    svc.run_forever()


def cmd_run_now(args) -> None:
    _check_api_key()
    from orchestrator.orchestrator import RootOrchestrator
    from rich.progress import Progress, SpinnerColumn, TextColumn
    console.print("[bold green]Running full pipeline now...[/]")
    orchestrator = RootOrchestrator()
    ctx = orchestrator.run_full_pipeline()
    elapsed = ctx.elapsed_seconds()
    console.print(f"[bold green]Done![/] Run ID: {ctx.run_id[:8]} | {elapsed:.1f}s")


def cmd_run_tier(args) -> None:
    _check_api_key()
    tier = args.tier
    if tier not in ("past", "present", "future"):
        console.print(f"[red]Unknown tier: {tier}[/] — choose from: past, present, future")
        sys.exit(1)
    from orchestrator.orchestrator import RootOrchestrator
    console.print(f"[green]Running {tier} tier...[/]")
    orchestrator = RootOrchestrator()
    orchestrator.run_tier(tier)
    console.print(f"[bold green]{tier.capitalize()} tier complete.[/]")


def cmd_run_agent(args) -> None:
    _check_api_key()
    agent_name = args.agent
    from orchestrator.orchestrator import RootOrchestrator
    console.print(f"[green]Running agent: {agent_name}[/]")
    orchestrator = RootOrchestrator()
    orchestrator.run_agent(agent_name)
    console.print(f"[bold green]Agent '{agent_name}' complete.[/]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI-Agents — 3-tier automated intelligence system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("daemon", help="Start the scheduler daemon")
    subparsers.add_parser("run-now", help="Run the full pipeline immediately")

    tier_parser = subparsers.add_parser("run-tier", help="Run a single tier")
    tier_parser.add_argument("tier", choices=["past", "present", "future"])

    agent_parser = subparsers.add_parser("run-agent", help="Run a single agent")
    agent_parser.add_argument("agent", help="Agent name (e.g. memory_keeper, news_scout)")

    args = parser.parse_args()

    dispatch = {
        "daemon": cmd_daemon,
        "run-now": cmd_run_now,
        "run-tier": cmd_run_tier,
        "run-agent": cmd_run_agent,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()

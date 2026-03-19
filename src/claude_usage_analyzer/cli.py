"""CLI entry point for claude-usage-analyzer."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from claude_usage_analyzer.analyzers import UsageAnalyzer
from claude_usage_analyzer.exporters import get_exporter
from claude_usage_analyzer.models import AnalysisResult
from claude_usage_analyzer.parsers import parse_all

console = Console()


@click.group()
@click.version_option()
def main():
    """Analyze Claude Code CLI session logs."""


@main.command()
@click.argument("path", default="~/.claude")
@click.option("--days", default=None, type=int, help="Only analyze last N days.")
@click.option("--top", default=10, type=int, help="Show top N sessions.")
def analyze(path: str, days: int | None, top: int):
    """Analyze session logs and display results."""
    result = _run_analysis(path, days)
    if result is None:
        return
    render_rich(result, top)


@main.command()
@click.argument("path", default="~/.claude")
@click.option("--format", "fmt", type=click.Choice(["json", "csv", "html"]), default="json")
@click.option("--output", "-o", default=None, help="Output file path.")
@click.option("--days", default=None, type=int, help="Only analyze last N days.")
def export(path: str, fmt: str, output: str | None, days: int | None):
    """Export usage report to file."""
    result = _run_analysis(path, days)
    if result is None:
        return

    if output is None:
        output = f"claude-usage-report.{fmt}"

    exporter = get_exporter(fmt)
    out_path = Path(output)
    exporter.export(result, out_path)
    console.print(f"Report exported to: {out_path.resolve()}")


def _run_analysis(path: str, days: int | None) -> AnalysisResult | None:
    log_dir = Path(path).expanduser()
    try:
        parse_result = parse_all(log_dir)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        return None

    if not parse_result.sessions:
        console.print("No session logs found.")
        return None

    if parse_result.warnings:
        console.print(f"[yellow]{len(parse_result.warnings)} warning(s) during parsing[/yellow]")

    return UsageAnalyzer().analyze(parse_result, days=days)


def render_rich(result: AnalysisResult, top: int = 10) -> None:
    """Render analysis result as Rich tables to the terminal."""
    ts = result.token_summary
    period = f"{result.analysis_period[0]} ~ {result.analysis_period[1]}"

    # Summary
    console.print()
    console.print(f"[bold]Claude Usage Report[/bold]  ({period})")
    sub_info = f"  |  Subagents: {result.total_subagents}" if result.total_subagents else ""
    cost_info = f"  |  Est. Cost: ${result.total_cost_usd:,.2f}" if result.total_cost_usd else ""
    console.print(f"Sessions: {result.total_sessions}  |  Messages: {result.total_messages}{sub_info}{cost_info}")
    console.print()

    # Token Summary
    t = Table(title="Token Summary")
    t.add_column("Metric", style="cyan")
    t.add_column("Tokens", justify="right", style="green")
    t.add_column("Est. Cost", justify="right", style="yellow")
    t.add_row("Input", f"{ts.total_input:,}", "")
    t.add_row("Output", f"{ts.total_output:,}", "")
    t.add_row("Cache Read", f"{ts.total_cache_read:,}", "")
    t.add_row("Cache Creation", f"{ts.total_cache_creation:,}", "")
    t.add_row("[bold]Total[/bold]", f"[bold]{ts.total_all:,}[/bold]",
              f"[bold]${ts.cost_usd:,.2f}[/bold]")
    console.print(t)
    console.print()

    # Model Distribution
    if result.model_distribution:
        t = Table(title="Model Distribution")
        t.add_column("Model", style="cyan")
        t.add_column("Input", justify="right")
        t.add_column("Output", justify="right")
        t.add_column("Sessions", justify="right")
        t.add_column("Messages", justify="right")
        t.add_column("%", justify="right")
        t.add_column("Cost", justify="right", style="yellow")
        for m in result.model_distribution:
            t.add_row(m.model, f"{m.input_tokens:,}", f"{m.output_tokens:,}",
                       str(m.session_count), str(m.message_count), f"{m.percentage}%",
                       f"${m.cost_usd:,.2f}")
        console.print(t)
        console.print()

    # Project Distribution
    if result.project_distribution:
        t = Table(title="Project Distribution")
        t.add_column("Project", style="cyan")
        t.add_column("Tokens", justify="right")
        t.add_column("Sessions", justify="right")
        t.add_column("Messages", justify="right")
        t.add_column("%", justify="right")
        t.add_column("Cost", justify="right", style="yellow")
        for p in result.project_distribution:
            t.add_row(p.project, f"{p.total_tokens:,}", str(p.session_count),
                       str(p.message_count), f"{p.percentage}%", f"${p.cost_usd:,.2f}")
        console.print(t)
        console.print()

    # Daily Trends (last 14 days max)
    if result.daily_trends:
        t = Table(title="Daily Trends")
        t.add_column("Date", style="cyan")
        t.add_column("Tokens", justify="right")
        t.add_column("Sessions", justify="right")
        t.add_column("Messages", justify="right")
        t.add_column("Cost", justify="right", style="yellow")
        for d in result.daily_trends[-14:]:
            t.add_row(d.date, f"{d.total_tokens:,}", str(d.session_count),
                       str(d.message_count), f"${d.cost_usd:,.2f}")
        console.print(t)
        console.print()

    # Top Sessions
    if result.session_overviews:
        t = Table(title=f"Top {top} Sessions (by tokens)")
        t.add_column("Session", style="cyan")
        t.add_column("Project")
        t.add_column("Model")
        t.add_column("Duration", justify="right")
        t.add_column("Msgs", justify="right")
        t.add_column("Tools", justify="right")
        t.add_column("Tokens", justify="right", style="green")
        t.add_column("Cost", justify="right", style="yellow")
        for s in result.session_overviews[:top]:
            dur = _format_duration(s.duration_seconds)
            sid = s.session_id[:8] + "..."
            t.add_row(sid, s.project, s.model or "", dur,
                       str(s.message_count), str(s.tool_call_count),
                       f"{s.total_tokens:,}", f"${s.cost_usd:,.2f}")
        console.print(t)
        console.print()

    # Subagent Distribution
    if result.subagent_distribution:
        t = Table(title="Subagent Distribution")
        t.add_column("Agent Type", style="cyan")
        t.add_column("Count", justify="right")
        t.add_column("Total Tokens", justify="right")
        t.add_column("Avg Tokens", justify="right")
        t.add_column("Messages", justify="right")
        t.add_column("%", justify="right", style="yellow")
        for sa in result.subagent_distribution:
            t.add_row(sa.agent_type, str(sa.count), f"{sa.total_tokens:,}",
                       f"{sa.avg_tokens:,}", str(sa.total_messages), f"{sa.percentage}%")
        console.print(t)
        console.print()

    # Hourly Distribution
    if result.hourly_distribution:
        t = Table(title="Hourly Activity")
        t.add_column("Hour", style="cyan")
        t.add_column("Sessions", justify="right")
        t.add_column("Messages", justify="right")
        t.add_column("Bar")
        max_msgs = max(h.message_count for h in result.hourly_distribution) or 1
        for h in result.hourly_distribution:
            bar_len = int(h.message_count / max_msgs * 20)
            bar = "█" * bar_len
            t.add_row(f"{h.hour:02d}:00", str(h.session_count),
                       str(h.message_count), f"[green]{bar}[/green]")
        console.print(t)


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds / 60:.0f}m"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    return f"{hours}h{mins}m"


if __name__ == "__main__":
    main()

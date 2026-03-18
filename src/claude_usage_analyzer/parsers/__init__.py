"""Parsers package — unified log parsing interface."""

from __future__ import annotations

from pathlib import Path

from claude_usage_analyzer.models import ParseResult
from claude_usage_analyzer.parsers.discovery import DiscoveredLogs, LogDiscovery
from claude_usage_analyzer.parsers.history import HistoryParser
from claude_usage_analyzer.parsers.session_log import SessionLogParser
from claude_usage_analyzer.parsers.session_meta import SessionMetaParser
from claude_usage_analyzer.parsers.stats_cache import StatsCacheParser

__all__ = [
    "parse_all",
    "DiscoveredLogs",
    "LogDiscovery",
    "HistoryParser",
    "SessionLogParser",
    "SessionMetaParser",
    "StatsCacheParser",
]


def parse_all(claude_dir: Path | str = "~/.claude") -> ParseResult:
    """Parse all Claude Code CLI logs from the given directory."""
    claude_dir = Path(claude_dir).expanduser()

    discovery = LogDiscovery()
    logs = discovery.discover(claude_dir)

    result = ParseResult()

    # Session transcripts
    if logs.session_logs:
        sessions, warnings = SessionLogParser().parse(logs.session_logs)
        result.sessions = sessions
        result.warnings.extend(warnings)

    # Session metadata
    if logs.session_metas:
        metas, warnings = SessionMetaParser().parse(logs.session_metas)
        result.session_metas = metas
        result.warnings.extend(warnings)

    # Command history
    if logs.history:
        commands, warnings = HistoryParser().parse(logs.history)
        result.commands = commands
        result.warnings.extend(warnings)

    # Stats cache
    if logs.stats_cache:
        stats, warnings = StatsCacheParser().parse(logs.stats_cache)
        result.stats = stats
        result.warnings.extend(warnings)

    return result

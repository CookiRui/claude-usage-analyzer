"""Log file discovery — scans ~/.claude/ for all log sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DiscoveredLogs:
    session_logs: list[Path] = field(default_factory=list)
    stats_cache: Path | None = None
    session_metas: list[Path] = field(default_factory=list)
    history: Path | None = None


class LogDiscovery:
    def discover(self, claude_dir: Path) -> DiscoveredLogs:
        claude_dir = Path(claude_dir)
        if not claude_dir.is_dir():
            raise FileNotFoundError(f"Log directory not found: {claude_dir}")

        result = DiscoveredLogs()

        # history.jsonl
        history = claude_dir / "history.jsonl"
        if history.is_file():
            result.history = history

        # stats-cache.json
        stats = claude_dir / "stats-cache.json"
        if stats.is_file():
            result.stats_cache = stats

        # sessions/*.json
        sessions_dir = claude_dir / "sessions"
        if sessions_dir.is_dir():
            result.session_metas = sorted(sessions_dir.glob("*.json"))

        # projects/*/*.jsonl (session transcripts)
        projects_dir = claude_dir / "projects"
        if projects_dir.is_dir():
            result.session_logs = sorted(projects_dir.glob("*/*.jsonl"))

        return result

"""Log file discovery — scans ~/.claude/ for all log sources."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from claude_usage_analyzer.models import SubagentFile


@dataclass
class DiscoveredLogs:
    session_logs: list[Path] = field(default_factory=list)
    stats_cache: Path | None = None
    session_metas: list[Path] = field(default_factory=list)
    history: Path | None = None
    subagent_files: list[SubagentFile] = field(default_factory=list)


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

            # projects/*/*/subagents/agent-*.jsonl (subagent transcripts)
            for jsonl in sorted(projects_dir.glob("*/*/subagents/agent-*.jsonl")):
                agent_id = self._extract_agent_id(jsonl.stem)
                if agent_id is None:
                    continue
                meta = jsonl.with_suffix("").with_suffix(".meta.json")
                # session dir is subagents' grandparent; project is one more level up
                session_dir = jsonl.parent.parent
                session_id = session_dir.name
                project = session_dir.parent.name
                result.subagent_files.append(SubagentFile(
                    jsonl_path=jsonl,
                    meta_path=meta if meta.is_file() else None,
                    session_id=session_id,
                    project=project,
                ))

        return result

    @staticmethod
    def _extract_agent_id(stem: str) -> str | None:
        """Extract agent ID from filename like 'agent-abc123'."""
        m = re.match(r"^agent-(.+)$", stem)
        return m.group(1) if m else None

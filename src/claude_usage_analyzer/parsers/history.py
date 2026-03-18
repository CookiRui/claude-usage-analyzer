"""Parser for history.jsonl — command history."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from claude_usage_analyzer.models import CommandRecord, ParseWarning


class HistoryParser:
    def parse(self, path: Path) -> tuple[list[CommandRecord], list[ParseWarning]]:
        path = Path(path)
        records: list[CommandRecord] = []
        warnings: list[ParseWarning] = []

        if not path.is_file():
            warnings.append(ParseWarning(str(path), None, f"File not found: {path}"))
            return records, warnings

        with open(path, encoding="utf-8", errors="replace") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    ts_ms = data["timestamp"]
                    records.append(CommandRecord(
                        display=data.get("display", ""),
                        timestamp=datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
                        project=data.get("project", ""),
                        session_id=data.get("sessionId", ""),
                    ))
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    warnings.append(ParseWarning(str(path), line_num, f"JSON parse error: {e}"))

        return records, warnings

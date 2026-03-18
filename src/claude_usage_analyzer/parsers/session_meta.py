"""Parser for sessions/*.json — session metadata."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from claude_usage_analyzer.models import ParseWarning, SessionMeta


class SessionMetaParser:
    def parse(self, paths: list[Path]) -> tuple[list[SessionMeta], list[ParseWarning]]:
        metas: list[SessionMeta] = []
        warnings: list[ParseWarning] = []

        for path in paths:
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
                ts_ms = data["startedAt"]
                metas.append(SessionMeta(
                    pid=data["pid"],
                    session_id=data["sessionId"],
                    cwd=data.get("cwd", ""),
                    started_at=datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
                ))
            except (json.JSONDecodeError, KeyError, TypeError, OSError) as e:
                warnings.append(ParseWarning(str(path), None, f"Failed to parse: {e}"))

        return metas, warnings

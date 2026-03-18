"""Parser for stats-cache.json — aggregated usage statistics."""

from __future__ import annotations

import json
from pathlib import Path

from claude_usage_analyzer.models import (
    DailyActivity,
    ModelTokenStats,
    ParseWarning,
    StatsCache,
)


class StatsCacheParser:
    def parse(self, path: Path) -> tuple[StatsCache | None, list[ParseWarning]]:
        path = Path(path)
        warnings: list[ParseWarning] = []

        if not path.is_file():
            warnings.append(ParseWarning(str(path), None, f"File not found: {path}"))
            return None, warnings

        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            warnings.append(ParseWarning(str(path), None, f"Failed to parse: {e}"))
            return None, warnings

        daily_activity = [
            DailyActivity(
                date=d.get("date", ""),
                message_count=d.get("messageCount", 0),
                session_count=d.get("sessionCount", 0),
                tool_call_count=d.get("toolCallCount", 0),
            )
            for d in data.get("dailyActivity", [])
        ]

        model_usage = [
            ModelTokenStats(
                model=model_name,
                input_tokens=stats.get("inputTokens", 0),
                output_tokens=stats.get("outputTokens", 0),
                cache_read_tokens=stats.get("cacheReadInputTokens", 0),
                cache_creation_tokens=stats.get("cacheCreationInputTokens", 0),
            )
            for model_name, stats in data.get("modelUsage", {}).items()
        ]

        stats = StatsCache(
            version=data.get("version", 0),
            last_computed_date=data.get("lastComputedDate", ""),
            total_sessions=data.get("totalSessions", 0),
            total_messages=data.get("totalMessages", 0),
            daily_activity=daily_activity,
            model_usage=model_usage,
        )

        return stats, warnings

"""CSV exporter — writes analysis data as a multi-section CSV."""

from __future__ import annotations

import csv
from pathlib import Path

from claude_usage_analyzer.exporters import BaseExporter
from claude_usage_analyzer.models import AnalysisResult


class CsvExporter(BaseExporter):
    def export(self, data: AnalysisResult, output: Path) -> None:
        output = Path(output)
        with open(output, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)

            # Section: Summary
            writer.writerow(["# Summary"])
            writer.writerow(["metric", "value"])
            writer.writerow(["total_sessions", data.total_sessions])
            writer.writerow(["total_messages", data.total_messages])
            writer.writerow(["total_input_tokens", data.token_summary.total_input])
            writer.writerow(["total_output_tokens", data.token_summary.total_output])
            writer.writerow(["total_cache_read_tokens", data.token_summary.total_cache_read])
            writer.writerow(["total_cache_creation_tokens", data.token_summary.total_cache_creation])
            writer.writerow(["total_all_tokens", data.token_summary.total_all])
            writer.writerow(["period_start", data.analysis_period[0]])
            writer.writerow(["period_end", data.analysis_period[1]])
            writer.writerow([])

            # Section: Model Distribution
            writer.writerow(["# Model Distribution"])
            writer.writerow(["model", "input_tokens", "output_tokens", "session_count",
                             "message_count", "percentage"])
            for m in data.model_distribution:
                writer.writerow([m.model, m.input_tokens, m.output_tokens,
                                 m.session_count, m.message_count, m.percentage])
            writer.writerow([])

            # Section: Project Distribution
            writer.writerow(["# Project Distribution"])
            writer.writerow(["project", "total_tokens", "session_count",
                             "message_count", "percentage"])
            for p in data.project_distribution:
                writer.writerow([p.project, p.total_tokens, p.session_count,
                                 p.message_count, p.percentage])
            writer.writerow([])

            # Section: Daily Trends
            writer.writerow(["# Daily Trends"])
            writer.writerow(["date", "total_tokens", "session_count", "message_count"])
            for d in data.daily_trends:
                writer.writerow([d.date, d.total_tokens, d.session_count, d.message_count])
            writer.writerow([])

            # Section: Session Overviews
            writer.writerow(["# Session Overviews"])
            writer.writerow(["session_id", "project", "model", "start_time",
                             "duration_seconds", "message_count", "tool_call_count",
                             "total_tokens"])
            for s in data.session_overviews:
                start = s.start_time.isoformat() if s.start_time else ""
                writer.writerow([s.session_id, s.project, s.model or "", start,
                                 s.duration_seconds, s.message_count,
                                 s.tool_call_count, s.total_tokens])

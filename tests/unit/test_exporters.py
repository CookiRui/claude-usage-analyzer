"""Tests for exporters."""

import csv
import json
from pathlib import Path

import pytest

from claude_usage_analyzer.exporters import BaseExporter, get_exporter
from claude_usage_analyzer.exporters.csv_exporter import CsvExporter
from claude_usage_analyzer.exporters.html_exporter import HtmlExporter
from claude_usage_analyzer.exporters.json_exporter import JsonExporter
from claude_usage_analyzer.models import (
    AnalysisResult,
    DailyTrend,
    ModelDistribution,
    ProjectDistribution,
    SessionOverview,
    TokenSummary,
)


@pytest.fixture
def sample_result() -> AnalysisResult:
    return AnalysisResult(
        token_summary=TokenSummary(
            total_input=5000, total_output=2000,
            total_cache_read=10000, total_cache_creation=500,
        ),
        model_distribution=[
            ModelDistribution("claude-opus-4-6", input_tokens=3000, output_tokens=1500,
                              session_count=5, message_count=20, percentage=75.0),
            ModelDistribution("claude-sonnet-4-5", input_tokens=2000, output_tokens=500,
                              session_count=3, message_count=10, percentage=25.0),
        ],
        project_distribution=[
            ProjectDistribution("my-project", total_tokens=12000, session_count=5,
                                message_count=20, percentage=80.0),
        ],
        daily_trends=[
            DailyTrend("2026-03-18", total_tokens=8000, session_count=3, message_count=15),
            DailyTrend("2026-03-19", total_tokens=4000, session_count=2, message_count=10),
        ],
        session_overviews=[
            SessionOverview("s1", "my-project", "claude-opus-4-6",
                            duration_seconds=1800, message_count=10,
                            tool_call_count=5, total_tokens=8000),
        ],
        total_sessions=8,
        total_messages=30,
        analysis_period=("2026-03-18", "2026-03-19"),
    )


class TestGetExporter:
    def test_json(self):
        assert isinstance(get_exporter("json"), JsonExporter)

    def test_csv(self):
        assert isinstance(get_exporter("csv"), CsvExporter)

    def test_html(self):
        assert isinstance(get_exporter("html"), HtmlExporter)

    def test_unknown_raises(self):
        with pytest.raises(ValueError):
            get_exporter("xml")


class TestJsonExporter:
    def test_export(self, sample_result: AnalysisResult, tmp_path: Path):
        out = tmp_path / "report.json"
        JsonExporter().export(sample_result, out)
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["total_sessions"] == 8
        assert data["token_summary"]["total_input"] == 5000
        assert len(data["model_distribution"]) == 2
        assert len(data["daily_trends"]) == 2


class TestCsvExporter:
    def test_export(self, sample_result: AnalysisResult, tmp_path: Path):
        out = tmp_path / "report.csv"
        CsvExporter().export(sample_result, out)
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        # Should contain headers and data
        assert "model" in content.lower()
        assert "claude-opus-4-6" in content

    def test_parseable_csv(self, sample_result: AnalysisResult, tmp_path: Path):
        out = tmp_path / "report.csv"
        CsvExporter().export(sample_result, out)
        with open(out, encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) > 1  # header + at least 1 data row


class TestHtmlExporter:
    def test_export(self, sample_result: AnalysisResult, tmp_path: Path):
        out = tmp_path / "report.html"
        HtmlExporter().export(sample_result, out)
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "<html" in content
        assert "claude-opus-4-6" in content
        assert "5,000" in content or "5000" in content

    def test_self_contained(self, sample_result: AnalysisResult, tmp_path: Path):
        out = tmp_path / "report.html"
        HtmlExporter().export(sample_result, out)
        content = out.read_text(encoding="utf-8")
        assert "<style" in content  # inline CSS
        assert "http" not in content.split("<style")[0]  # no external CSS links before style

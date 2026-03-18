"""Integration tests for CLI commands."""

import json
from pathlib import Path

from click.testing import CliRunner

from claude_usage_analyzer.cli import main

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestAnalyzeCommand:
    def test_analyze_with_fixtures(self):
        runner = CliRunner()
        result = runner.invoke(main, ["analyze", str(FIXTURES)])
        assert result.exit_code == 0
        # Should contain Rich table output
        assert "Token Summary" in result.output
        assert "Model Distribution" in result.output
        assert "Project Distribution" in result.output
        assert "Daily Trends" in result.output
        assert "Subagent" in result.output

    def test_analyze_nonexistent_path(self):
        runner = CliRunner()
        result = runner.invoke(main, ["analyze", "/nonexistent/path"])
        assert "Error" in result.output or "not found" in result.output.lower()

    def test_analyze_with_days(self):
        runner = CliRunner()
        # days=1 should filter out our fixture data (dated 2026-03-18)
        # This won't crash even if no data matches
        result = runner.invoke(main, ["analyze", str(FIXTURES), "--days", "1"])
        assert result.exit_code == 0


class TestExportCommand:
    def test_export_json(self, tmp_path: Path):
        out = tmp_path / "report.json"
        runner = CliRunner()
        result = runner.invoke(main, ["export", str(FIXTURES), "--format", "json", "-o", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "token_summary" in data
        assert data["total_sessions"] >= 2

    def test_export_csv(self, tmp_path: Path):
        out = tmp_path / "report.csv"
        runner = CliRunner()
        result = runner.invoke(main, ["export", str(FIXTURES), "--format", "csv", "-o", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "model" in content.lower()

    def test_export_html(self, tmp_path: Path):
        out = tmp_path / "report.html"
        runner = CliRunner()
        result = runner.invoke(main, ["export", str(FIXTURES), "--format", "html", "-o", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "<html" in content

"""Tests for all parsers."""

from pathlib import Path

import pytest

from claude_usage_analyzer.models import (
    CommandRecord,
    ParseResult,
    SessionMeta,
    SessionTranscript,
    StatsCache,
)
from claude_usage_analyzer.parsers.discovery import DiscoveredLogs, LogDiscovery
from claude_usage_analyzer.parsers.history import HistoryParser
from claude_usage_analyzer.parsers.session_log import SessionLogParser
from claude_usage_analyzer.parsers.session_meta import SessionMetaParser
from claude_usage_analyzer.parsers.stats_cache import StatsCacheParser

FIXTURES = Path(__file__).parent.parent / "fixtures"


# ============================================================
# LogDiscovery
# ============================================================

class TestLogDiscovery:
    def test_discover_finds_all_logs(self):
        discovery = LogDiscovery()
        result = discovery.discover(FIXTURES)
        assert result.history is not None
        assert result.history.name == "history.jsonl"
        assert result.stats_cache is not None
        assert result.stats_cache.name == "stats-cache.json"
        assert len(result.session_metas) >= 2  # 12345.json, 67890.json (may include bad.json)
        assert len(result.session_logs) >= 2  # session-001.jsonl, session-002.jsonl

    def test_discover_nonexistent_dir_raises(self):
        discovery = LogDiscovery()
        with pytest.raises(FileNotFoundError):
            discovery.discover(Path("/nonexistent/path"))


# ============================================================
# HistoryParser
# ============================================================

class TestHistoryParser:
    def test_parse_normal_lines(self):
        parser = HistoryParser()
        records, warnings = parser.parse(FIXTURES / "history.jsonl")
        # 5 lines total, 1 broken → 4 valid
        assert len(records) == 4
        assert records[0].display == "/init"
        assert records[0].session_id == "aaa11111-1111-1111-1111-111111111111"
        assert records[1].display == "help me fix the bug"
        assert records[1].project == "E:\\Work\\TestProject"

    def test_broken_line_produces_warning(self):
        parser = HistoryParser()
        records, warnings = parser.parse(FIXTURES / "history.jsonl")
        assert len(warnings) == 1
        assert warnings[0].line == 4
        assert "json" in warnings[0].message.lower() or "JSON" in warnings[0].message

    def test_nonexistent_file_returns_empty_with_warning(self):
        parser = HistoryParser()
        records, warnings = parser.parse(Path("/nonexistent/history.jsonl"))
        assert records == []
        assert len(warnings) == 1


# ============================================================
# SessionMetaParser
# ============================================================

class TestSessionMetaParser:
    def test_parse_valid_files(self):
        paths = [FIXTURES / "sessions" / "12345.json", FIXTURES / "sessions" / "67890.json"]
        parser = SessionMetaParser()
        metas, warnings = parser.parse(paths)
        assert len(metas) == 2
        assert metas[0].pid == 12345
        assert metas[0].session_id == "bbb11111-1111-1111-1111-111111111111"
        assert metas[1].pid == 67890

    def test_bad_file_produces_warning(self):
        paths = [FIXTURES / "sessions" / "bad.json"]
        parser = SessionMetaParser()
        metas, warnings = parser.parse(paths)
        assert len(metas) == 0
        assert len(warnings) == 1


# ============================================================
# StatsCacheParser
# ============================================================

class TestStatsCacheParser:
    def test_parse_valid(self):
        parser = StatsCacheParser()
        stats, warnings = parser.parse(FIXTURES / "stats-cache.json")
        assert stats is not None
        assert stats.version == 2
        assert stats.total_sessions == 49
        assert stats.total_messages == 22354
        assert stats.last_computed_date == "2026-02-23"
        assert len(stats.daily_activity) == 2
        assert stats.daily_activity[0].message_count == 525
        assert len(stats.model_usage) == 2
        assert warnings == []

    def test_nonexistent_returns_none_with_warning(self):
        parser = StatsCacheParser()
        stats, warnings = parser.parse(Path("/nonexistent/stats-cache.json"))
        assert stats is None
        assert len(warnings) == 1


# ============================================================
# SessionLogParser
# ============================================================

class TestSessionLogParser:
    def test_parse_user_messages(self):
        parser = SessionLogParser()
        sessions, warnings = parser.parse([FIXTURES / "projects" / "test-project" / "session-001.jsonl"])
        assert len(sessions) == 1
        session = sessions[0]
        user_msgs = [m for m in session.messages if m.role == "user"]
        assert len(user_msgs) == 3
        assert user_msgs[0].content_preview == "help me fix the login bug"

    def test_parse_assistant_messages_with_tokens(self):
        parser = SessionLogParser()
        sessions, warnings = parser.parse([FIXTURES / "projects" / "test-project" / "session-001.jsonl"])
        session = sessions[0]
        assistant_msgs = [m for m in session.messages if m.role == "assistant"]
        assert len(assistant_msgs) == 2
        first = assistant_msgs[0]
        assert first.token_usage is not None
        assert first.token_usage.input_tokens == 1500
        assert first.token_usage.output_tokens == 350
        assert first.token_usage.cache_read_tokens == 50000
        assert first.model == "claude-opus-4-6"

    def test_extract_tool_calls(self):
        parser = SessionLogParser()
        sessions, warnings = parser.parse([FIXTURES / "projects" / "test-project" / "session-001.jsonl"])
        session = sessions[0]
        assistant_msgs = [m for m in session.messages if m.role == "assistant"]
        assert "Read" in assistant_msgs[0].tool_calls
        assert "Edit" in assistant_msgs[1].tool_calls

    def test_session_grouping(self):
        parser = SessionLogParser()
        paths = [
            FIXTURES / "projects" / "test-project" / "session-001.jsonl",
            FIXTURES / "projects" / "test-project" / "session-002.jsonl",
        ]
        sessions, warnings = parser.parse(paths)
        assert len(sessions) == 2
        ids = {s.session_id for s in sessions}
        assert "ddd11111-1111-1111-1111-111111111111" in ids
        assert "ddd22222-2222-2222-2222-222222222222" in ids

    def test_session_total_tokens(self):
        parser = SessionLogParser()
        sessions, warnings = parser.parse([FIXTURES / "projects" / "test-project" / "session-001.jsonl"])
        session = sessions[0]
        # Two assistant messages: (1500+350+50000+200) + (2000+500+52000+100) = 106650
        assert session.total_tokens.input_tokens == 3500
        assert session.total_tokens.output_tokens == 850

    def test_session_time_range(self):
        parser = SessionLogParser()
        sessions, warnings = parser.parse([FIXTURES / "projects" / "test-project" / "session-001.jsonl"])
        session = sessions[0]
        assert session.start_time is not None
        assert session.end_time is not None
        assert session.start_time < session.end_time

    def test_broken_line_produces_warning(self):
        parser = SessionLogParser()
        sessions, warnings = parser.parse([FIXTURES / "projects" / "test-project" / "session-001.jsonl"])
        assert len(warnings) == 1
        assert warnings[0].line == 5

    def test_session_model(self):
        parser = SessionLogParser()
        sessions, warnings = parser.parse([FIXTURES / "projects" / "test-project" / "session-002.jsonl"])
        assert sessions[0].model == "claude-sonnet-4-5-20250929"

    def test_project_from_path(self):
        parser = SessionLogParser()
        sessions, warnings = parser.parse([FIXTURES / "projects" / "test-project" / "session-001.jsonl"])
        assert sessions[0].project == "test-project"


# ============================================================
# parse_all integration
# ============================================================

class TestParseAll:
    def test_end_to_end(self):
        from claude_usage_analyzer.parsers import parse_all

        result = parse_all(FIXTURES)
        assert isinstance(result, ParseResult)
        assert len(result.sessions) >= 2
        assert len(result.session_metas) >= 2
        assert len(result.commands) >= 4
        assert result.stats is not None
        assert result.stats.total_sessions == 49
        # Should have some warnings (broken lines in history + session-001)
        assert len(result.warnings) >= 2

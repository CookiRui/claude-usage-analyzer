"""Tests for data models."""

from datetime import datetime, timezone

from claude_usage_analyzer.models import (
    CommandRecord,
    DailyActivity,
    Message,
    ModelTokenStats,
    ParseResult,
    ParseWarning,
    SessionMeta,
    SessionTranscript,
    StatsCache,
    TokenUsage,
)


class TestTokenUsage:
    def test_defaults_to_zero(self):
        t = TokenUsage()
        assert t.input_tokens == 0
        assert t.output_tokens == 0
        assert t.cache_read_tokens == 0
        assert t.cache_creation_tokens == 0

    def test_total(self):
        t = TokenUsage(input_tokens=100, output_tokens=200, cache_read_tokens=300, cache_creation_tokens=50)
        assert t.total == 650

    def test_add(self):
        a = TokenUsage(input_tokens=100, output_tokens=200)
        b = TokenUsage(input_tokens=50, output_tokens=80, cache_read_tokens=10)
        result = a + b
        assert result.input_tokens == 150
        assert result.output_tokens == 280
        assert result.cache_read_tokens == 10


class TestMessage:
    def test_create(self):
        msg = Message(
            role="assistant",
            uuid="msg-1",
            timestamp=datetime(2026, 3, 18, tzinfo=timezone.utc),
            session_id="sess-1",
            content_preview="Hello",
            token_usage=TokenUsage(input_tokens=10),
            model="claude-opus-4-6",
            tool_calls=["Read", "Edit"],
        )
        assert msg.role == "assistant"
        assert msg.model == "claude-opus-4-6"
        assert len(msg.tool_calls) == 2

    def test_defaults(self):
        msg = Message(
            role="user",
            uuid="msg-2",
            timestamp=datetime(2026, 3, 18, tzinfo=timezone.utc),
            session_id="sess-1",
            content_preview="Hi",
        )
        assert msg.token_usage is None
        assert msg.model is None
        assert msg.tool_calls == []


class TestSessionTranscript:
    def test_create_empty(self):
        s = SessionTranscript(session_id="sess-1", project="test-project")
        assert s.messages == []
        assert s.total_tokens.total == 0
        assert s.start_time is None


class TestSessionMeta:
    def test_create(self):
        m = SessionMeta(
            pid=12345,
            session_id="sess-1",
            cwd="E:\\Work",
            started_at=datetime(2026, 3, 18, tzinfo=timezone.utc),
        )
        assert m.pid == 12345


class TestCommandRecord:
    def test_create(self):
        c = CommandRecord(
            display="/init",
            timestamp=datetime(2026, 3, 18, tzinfo=timezone.utc),
            project="C:\\Users\\admin",
            session_id="sess-1",
        )
        assert c.display == "/init"


class TestStatsCache:
    def test_create(self):
        s = StatsCache(
            version=2,
            last_computed_date="2026-02-23",
            total_sessions=49,
            total_messages=22354,
            daily_activity=[DailyActivity("2026-01-19", 525, 7, 86)],
            model_usage=[ModelTokenStats("claude-opus-4-6", input_tokens=100)],
        )
        assert s.total_sessions == 49
        assert len(s.daily_activity) == 1
        assert s.model_usage[0].model == "claude-opus-4-6"


class TestParseResult:
    def test_create_empty(self):
        r = ParseResult()
        assert r.sessions == []
        assert r.session_metas == []
        assert r.commands == []
        assert r.stats is None
        assert r.warnings == []

    def test_with_warnings(self):
        r = ParseResult(warnings=[ParseWarning("file.jsonl", 3, "bad json")])
        assert len(r.warnings) == 1
        assert r.warnings[0].line == 3

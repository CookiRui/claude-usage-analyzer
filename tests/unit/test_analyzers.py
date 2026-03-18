"""Tests for UsageAnalyzer."""

from datetime import datetime, timezone

from claude_usage_analyzer.analyzers.usage import UsageAnalyzer
from claude_usage_analyzer.models import (
    Message,
    ParseResult,
    SessionTranscript,
    SubagentTranscript,
    TokenUsage,
)


def _make_session(
    session_id: str,
    project: str,
    model: str,
    messages: list[Message] | None = None,
    start_hour: int = 10,
) -> SessionTranscript:
    """Helper to build a SessionTranscript for testing."""
    if messages is None:
        start = datetime(2026, 3, 18, start_hour, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 18, start_hour, 30, 0, tzinfo=timezone.utc)
        messages = [
            Message(
                role="user", uuid="u1", timestamp=start,
                session_id=session_id, content_preview="hello",
            ),
            Message(
                role="assistant", uuid="a1", timestamp=end,
                session_id=session_id, content_preview="hi",
                token_usage=TokenUsage(input_tokens=1000, output_tokens=500,
                                       cache_read_tokens=2000, cache_creation_tokens=100),
                model=model, tool_calls=["Read", "Edit"],
            ),
        ]
    total = TokenUsage()
    for m in messages:
        if m.token_usage:
            total = total + m.token_usage
    return SessionTranscript(
        session_id=session_id, project=project, messages=messages,
        total_tokens=total,
        start_time=messages[0].timestamp if messages else None,
        end_time=messages[-1].timestamp if messages else None,
        model=model,
    )


def _make_parse_result(*sessions: SessionTranscript) -> ParseResult:
    return ParseResult(sessions=list(sessions))


class TestTokenSummary:
    def test_single_session(self):
        s = _make_session("s1", "proj-a", "claude-opus-4-6")
        result = UsageAnalyzer().analyze(_make_parse_result(s))
        ts = result.token_summary
        assert ts.total_input == 1000
        assert ts.total_output == 500
        assert ts.total_cache_read == 2000
        assert ts.total_cache_creation == 100
        assert ts.total_all == 3600

    def test_multiple_sessions(self):
        s1 = _make_session("s1", "proj-a", "claude-opus-4-6")
        s2 = _make_session("s2", "proj-b", "claude-sonnet-4-5")
        result = UsageAnalyzer().analyze(_make_parse_result(s1, s2))
        assert result.token_summary.total_input == 2000
        assert result.token_summary.total_output == 1000


class TestModelDistribution:
    def test_groups_by_model(self):
        s1 = _make_session("s1", "proj-a", "claude-opus-4-6")
        s2 = _make_session("s2", "proj-a", "claude-opus-4-6")
        s3 = _make_session("s3", "proj-b", "claude-sonnet-4-5")
        result = UsageAnalyzer().analyze(_make_parse_result(s1, s2, s3))
        dist = {d.model: d for d in result.model_distribution}
        assert "claude-opus-4-6" in dist
        assert "claude-sonnet-4-5" in dist
        assert dist["claude-opus-4-6"].session_count == 2
        assert dist["claude-sonnet-4-5"].session_count == 1

    def test_percentage(self):
        s1 = _make_session("s1", "proj-a", "claude-opus-4-6")
        s2 = _make_session("s2", "proj-a", "claude-sonnet-4-5")
        result = UsageAnalyzer().analyze(_make_parse_result(s1, s2))
        total_pct = sum(d.percentage for d in result.model_distribution)
        assert abs(total_pct - 100.0) < 0.1


class TestProjectDistribution:
    def test_groups_by_project(self):
        s1 = _make_session("s1", "proj-a", "claude-opus-4-6")
        s2 = _make_session("s2", "proj-a", "claude-opus-4-6")
        s3 = _make_session("s3", "proj-b", "claude-sonnet-4-5")
        result = UsageAnalyzer().analyze(_make_parse_result(s1, s2, s3))
        dist = {d.project: d for d in result.project_distribution}
        assert dist["proj-a"].session_count == 2
        assert dist["proj-b"].session_count == 1

    def test_percentage(self):
        s1 = _make_session("s1", "proj-a", "claude-opus-4-6")
        s2 = _make_session("s2", "proj-b", "claude-sonnet-4-5")
        result = UsageAnalyzer().analyze(_make_parse_result(s1, s2))
        total_pct = sum(d.percentage for d in result.project_distribution)
        assert abs(total_pct - 100.0) < 0.1


class TestDailyTrends:
    def test_groups_by_date(self):
        s1 = _make_session("s1", "proj-a", "claude-opus-4-6")
        # s2 on a different day
        start2 = datetime(2026, 3, 19, 14, 0, 0, tzinfo=timezone.utc)
        end2 = datetime(2026, 3, 19, 14, 30, 0, tzinfo=timezone.utc)
        msgs2 = [
            Message(role="user", uuid="u2", timestamp=start2,
                    session_id="s2", content_preview="test"),
            Message(role="assistant", uuid="a2", timestamp=end2,
                    session_id="s2", content_preview="ok",
                    token_usage=TokenUsage(input_tokens=500, output_tokens=200),
                    model="claude-opus-4-6"),
        ]
        s2 = _make_session("s2", "proj-a", "claude-opus-4-6", messages=msgs2)
        result = UsageAnalyzer().analyze(_make_parse_result(s1, s2))
        assert len(result.daily_trends) == 2
        dates = {d.date for d in result.daily_trends}
        assert "2026-03-18" in dates
        assert "2026-03-19" in dates

    def test_sorted_by_date(self):
        start2 = datetime(2026, 3, 17, 8, 0, 0, tzinfo=timezone.utc)
        end2 = datetime(2026, 3, 17, 8, 30, 0, tzinfo=timezone.utc)
        msgs2 = [
            Message(role="user", uuid="u2", timestamp=start2,
                    session_id="s2", content_preview="x"),
            Message(role="assistant", uuid="a2", timestamp=end2,
                    session_id="s2", content_preview="y",
                    token_usage=TokenUsage(input_tokens=100), model="m"),
        ]
        s1 = _make_session("s1", "p", "m")  # 2026-03-18
        s2 = _make_session("s2", "p", "m", messages=msgs2)  # 2026-03-17
        result = UsageAnalyzer().analyze(_make_parse_result(s1, s2))
        assert result.daily_trends[0].date == "2026-03-17"
        assert result.daily_trends[1].date == "2026-03-18"


class TestSessionOverviews:
    def test_overview_fields(self):
        s = _make_session("s1", "proj-a", "claude-opus-4-6")
        result = UsageAnalyzer().analyze(_make_parse_result(s))
        assert len(result.session_overviews) == 1
        ov = result.session_overviews[0]
        assert ov.session_id == "s1"
        assert ov.project == "proj-a"
        assert ov.model == "claude-opus-4-6"
        assert ov.message_count == 2
        assert ov.tool_call_count == 2  # Read + Edit
        assert ov.duration_seconds == 1800.0  # 30 minutes
        assert ov.total_tokens == 3600

    def test_sorted_by_tokens_desc(self):
        s1 = _make_session("s1", "p", "m")  # 3600 tokens
        start2 = datetime(2026, 3, 18, 10, 0, 0, tzinfo=timezone.utc)
        end2 = datetime(2026, 3, 18, 10, 5, 0, tzinfo=timezone.utc)
        msgs2 = [
            Message(role="user", uuid="u", timestamp=start2,
                    session_id="s2", content_preview="x"),
            Message(role="assistant", uuid="a", timestamp=end2,
                    session_id="s2", content_preview="y",
                    token_usage=TokenUsage(input_tokens=10000, output_tokens=5000),
                    model="m"),
        ]
        s2 = _make_session("s2", "p", "m", messages=msgs2)  # 15000 tokens
        result = UsageAnalyzer().analyze(_make_parse_result(s1, s2))
        assert result.session_overviews[0].session_id == "s2"  # more tokens first


class TestHourlyDistribution:
    def test_distribution(self):
        s1 = _make_session("s1", "p", "m", start_hour=10)
        s2 = _make_session("s2", "p", "m", start_hour=14)
        result = UsageAnalyzer().analyze(_make_parse_result(s1, s2))
        hours = {h.hour: h for h in result.hourly_distribution}
        assert hours[10].session_count >= 1
        assert hours[14].session_count >= 1


class TestDaysFilter:
    def test_filters_old_sessions(self):
        # Recent session
        s1 = _make_session("s1", "p", "m")  # 2026-03-18
        # Old session (60 days ago)
        old_start = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        old_end = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        msgs = [
            Message(role="user", uuid="u", timestamp=old_start,
                    session_id="s2", content_preview="old"),
            Message(role="assistant", uuid="a", timestamp=old_end,
                    session_id="s2", content_preview="old reply",
                    token_usage=TokenUsage(input_tokens=500), model="m"),
        ]
        s2 = _make_session("s2", "p", "m", messages=msgs)
        result = UsageAnalyzer().analyze(_make_parse_result(s1, s2), days=30)
        assert result.total_sessions == 1
        assert result.session_overviews[0].session_id == "s1"


class TestEmptyData:
    def test_empty_parse_result(self):
        result = UsageAnalyzer().analyze(ParseResult())
        assert result.total_sessions == 0
        assert result.total_messages == 0
        assert result.token_summary.total_all == 0
        assert result.model_distribution == []
        assert result.project_distribution == []
        assert result.daily_trends == []
        assert result.session_overviews == []

    def test_session_with_no_messages(self):
        s = SessionTranscript(session_id="s1", project="p")
        result = UsageAnalyzer().analyze(_make_parse_result(s))
        assert result.total_sessions == 1
        assert result.total_messages == 0

    def test_empty_subagents(self):
        result = UsageAnalyzer().analyze(ParseResult())
        assert result.subagent_distribution == []
        assert result.total_subagents == 0


class TestSubagentDistribution:
    def test_groups_by_type(self):
        sa1 = SubagentTranscript(
            agent_id="a1", session_id="s1", project="p",
            agent_type="Explore", description="explore",
            total_tokens=TokenUsage(input_tokens=500, output_tokens=100),
            messages=[],
        )
        sa2 = SubagentTranscript(
            agent_id="a2", session_id="s1", project="p",
            agent_type="Explore", description="explore again",
            total_tokens=TokenUsage(input_tokens=300, output_tokens=50),
            messages=[],
        )
        sa3 = SubagentTranscript(
            agent_id="a3", session_id="s1", project="p",
            agent_type="Plan", description="plan",
            total_tokens=TokenUsage(input_tokens=1000, output_tokens=200),
            messages=[],
        )
        data = ParseResult(subagents=[sa1, sa2, sa3])
        result = UsageAnalyzer().analyze(data)
        dist = {d.agent_type: d for d in result.subagent_distribution}
        assert "Explore" in dist
        assert "Plan" in dist
        assert dist["Explore"].count == 2
        assert dist["Plan"].count == 1
        assert result.total_subagents == 3

    def test_percentage(self):
        sa1 = SubagentTranscript(
            agent_id="a1", session_id="s1", project="p",
            agent_type="Explore", description="",
            total_tokens=TokenUsage(input_tokens=750, output_tokens=250),
        )
        sa2 = SubagentTranscript(
            agent_id="a2", session_id="s1", project="p",
            agent_type="Plan", description="",
            total_tokens=TokenUsage(input_tokens=750, output_tokens=250),
        )
        data = ParseResult(subagents=[sa1, sa2])
        result = UsageAnalyzer().analyze(data)
        total_pct = sum(d.percentage for d in result.subagent_distribution)
        assert abs(total_pct - 100.0) < 0.1

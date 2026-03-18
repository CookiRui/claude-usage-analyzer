"""Data models for Claude Code CLI log parsing and analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

    @property
    def total(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_tokens
            + self.cache_creation_tokens
        )

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
            cache_creation_tokens=self.cache_creation_tokens + other.cache_creation_tokens,
        )


@dataclass
class Message:
    role: str
    uuid: str
    timestamp: datetime
    session_id: str
    content_preview: str
    token_usage: TokenUsage | None = None
    model: str | None = None
    tool_calls: list[str] = field(default_factory=list)


@dataclass
class SessionTranscript:
    session_id: str
    project: str
    messages: list[Message] = field(default_factory=list)
    total_tokens: TokenUsage = field(default_factory=TokenUsage)
    start_time: datetime | None = None
    end_time: datetime | None = None
    model: str | None = None


@dataclass
class SessionMeta:
    pid: int
    session_id: str
    cwd: str
    started_at: datetime


@dataclass
class CommandRecord:
    display: str
    timestamp: datetime
    project: str
    session_id: str


@dataclass
class DailyActivity:
    date: str
    message_count: int
    session_count: int
    tool_call_count: int


@dataclass
class ModelTokenStats:
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0


@dataclass
class StatsCache:
    version: int
    last_computed_date: str
    total_sessions: int
    total_messages: int
    daily_activity: list[DailyActivity] = field(default_factory=list)
    model_usage: list[ModelTokenStats] = field(default_factory=list)


@dataclass
class ParseWarning:
    source: str
    line: int | None
    message: str


@dataclass
class ParseResult:
    sessions: list[SessionTranscript] = field(default_factory=list)
    session_metas: list[SessionMeta] = field(default_factory=list)
    commands: list[CommandRecord] = field(default_factory=list)
    stats: StatsCache | None = None
    subagents: list[SubagentTranscript] = field(default_factory=list)
    warnings: list[ParseWarning] = field(default_factory=list)


# ============================================================
# Subagent models
# ============================================================


@dataclass
class SubagentFile:
    jsonl_path: Path
    meta_path: Path | None
    session_id: str
    project: str


@dataclass
class SubagentTranscript:
    agent_id: str
    session_id: str
    project: str
    agent_type: str
    description: str
    messages: list[Message] = field(default_factory=list)
    total_tokens: TokenUsage = field(default_factory=TokenUsage)
    start_time: datetime | None = None
    end_time: datetime | None = None
    model: str | None = None


@dataclass
class SubagentDistribution:
    agent_type: str
    count: int = 0
    total_tokens: int = 0
    avg_tokens: int = 0
    total_messages: int = 0
    percentage: float = 0.0


# ============================================================
# Analysis result models
# ============================================================


@dataclass
class TokenSummary:
    total_input: int = 0
    total_output: int = 0
    total_cache_read: int = 0
    total_cache_creation: int = 0

    @property
    def total_all(self) -> int:
        return self.total_input + self.total_output + self.total_cache_read + self.total_cache_creation


@dataclass
class ModelDistribution:
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    session_count: int = 0
    message_count: int = 0
    percentage: float = 0.0


@dataclass
class ProjectDistribution:
    project: str
    total_tokens: int = 0
    session_count: int = 0
    message_count: int = 0
    percentage: float = 0.0


@dataclass
class DailyTrend:
    date: str
    total_tokens: int = 0
    session_count: int = 0
    message_count: int = 0


@dataclass
class SessionOverview:
    session_id: str
    project: str
    model: str | None = None
    start_time: datetime | None = None
    duration_seconds: float = 0.0
    message_count: int = 0
    tool_call_count: int = 0
    total_tokens: int = 0


@dataclass
class HourlyDistribution:
    hour: int
    session_count: int = 0
    message_count: int = 0


@dataclass
class AnalysisResult:
    token_summary: TokenSummary = field(default_factory=TokenSummary)
    model_distribution: list[ModelDistribution] = field(default_factory=list)
    project_distribution: list[ProjectDistribution] = field(default_factory=list)
    daily_trends: list[DailyTrend] = field(default_factory=list)
    session_overviews: list[SessionOverview] = field(default_factory=list)
    hourly_distribution: list[HourlyDistribution] = field(default_factory=list)
    subagent_distribution: list[SubagentDistribution] = field(default_factory=list)
    total_sessions: int = 0
    total_messages: int = 0
    total_subagents: int = 0
    analysis_period: tuple[str, str] = ("", "")

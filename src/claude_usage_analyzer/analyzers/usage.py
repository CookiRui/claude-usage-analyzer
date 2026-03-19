"""Core usage analyzer — computes all analysis dimensions from ParseResult."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from claude_usage_analyzer.models import (
    AnalysisResult,
    DailyTrend,
    HourlyDistribution,
    ModelDistribution,
    ParseResult,
    ProjectDistribution,
    SessionOverview,
    SessionTranscript,
    SubagentDistribution,
    SubagentTranscript,
    TokenSummary,
)
from claude_usage_analyzer.pricing import ModelPrice, compute_cost, get_model_price


class UsageAnalyzer:
    def analyze(
        self,
        data: ParseResult,
        days: int | None = None,
        pricing: dict[str, ModelPrice] | None = None,
    ) -> AnalysisResult:
        sessions = data.sessions

        # Filter by days if specified
        if days is not None and sessions:
            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
            sessions = [
                s for s in sessions
                if s.start_time is not None and s.start_time >= cutoff
            ]

        total_messages = sum(len(s.messages) for s in sessions)

        # Compute analysis period
        all_dates = [
            s.start_time.strftime("%Y-%m-%d")
            for s in sessions if s.start_time
        ]
        if all_dates:
            period = (min(all_dates), max(all_dates))
        else:
            period = ("", "")

        subagents = data.subagents

        token_summary = self._compute_token_summary(sessions, pricing)
        model_dist = self._compute_model_distribution(sessions, pricing)
        project_dist = self._compute_project_distribution(sessions, pricing)
        daily_trends = self._compute_daily_trends(sessions, pricing)
        session_overviews = self._compute_session_overviews(sessions, pricing)

        return AnalysisResult(
            token_summary=token_summary,
            model_distribution=model_dist,
            project_distribution=project_dist,
            daily_trends=daily_trends,
            session_overviews=session_overviews,
            hourly_distribution=self._compute_hourly_distribution(sessions),
            subagent_distribution=self._compute_subagent_distribution(subagents),
            total_sessions=len(sessions),
            total_messages=total_messages,
            total_cost_usd=token_summary.cost_usd,
            total_subagents=len(subagents),
            analysis_period=period,
        )

    def _compute_token_summary(
        self,
        sessions: list[SessionTranscript],
        pricing: dict[str, ModelPrice] | None = None,
    ) -> TokenSummary:
        total_in = total_out = total_cr = total_cc = 0
        total_cost = 0.0
        for s in sessions:
            total_in += s.total_tokens.input_tokens
            total_out += s.total_tokens.output_tokens
            total_cr += s.total_tokens.cache_read_tokens
            total_cc += s.total_tokens.cache_creation_tokens
            total_cost += self._session_cost(s, pricing)
        return TokenSummary(
            total_input=total_in,
            total_output=total_out,
            total_cache_read=total_cr,
            total_cache_creation=total_cc,
            cost_usd=round(total_cost, 4),
        )

    def _compute_model_distribution(
        self,
        sessions: list[SessionTranscript],
        pricing: dict[str, ModelPrice] | None = None,
    ) -> list[ModelDistribution]:
        model_data: dict[str, dict] = defaultdict(
            lambda: {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0,
                     "sessions": 0, "messages": 0}
        )
        for s in sessions:
            model = s.model or "unknown"
            model_data[model]["sessions"] += 1
            for msg in s.messages:
                if msg.model:
                    model_data[msg.model]["messages"] += 1
                    if msg.token_usage:
                        model_data[msg.model]["input"] += msg.token_usage.input_tokens
                        model_data[msg.model]["output"] += msg.token_usage.output_tokens
                        model_data[msg.model]["cache_read"] += msg.token_usage.cache_read_tokens
                        model_data[msg.model]["cache_write"] += msg.token_usage.cache_creation_tokens

        grand_total = sum(
            d["input"] + d["output"] for d in model_data.values()
        )

        result = []
        for model, d in model_data.items():
            model_total = d["input"] + d["output"]
            pct = (model_total / grand_total * 100) if grand_total > 0 else 0.0
            price = get_model_price(model, pricing)
            cost = compute_cost(d["input"], d["output"], d["cache_write"], d["cache_read"], price)
            result.append(ModelDistribution(
                model=model,
                input_tokens=d["input"],
                output_tokens=d["output"],
                session_count=d["sessions"],
                message_count=d["messages"],
                percentage=round(pct, 1),
                cost_usd=round(cost, 4),
            ))
        result.sort(key=lambda x: x.input_tokens + x.output_tokens, reverse=True)
        return result

    def _compute_project_distribution(
        self,
        sessions: list[SessionTranscript],
        pricing: dict[str, ModelPrice] | None = None,
    ) -> list[ProjectDistribution]:
        proj_data: dict[str, dict] = defaultdict(
            lambda: {"tokens": 0, "sessions": 0, "messages": 0, "cost": 0.0}
        )
        for s in sessions:
            proj_data[s.project]["sessions"] += 1
            proj_data[s.project]["messages"] += len(s.messages)
            proj_data[s.project]["tokens"] += s.total_tokens.total
            proj_data[s.project]["cost"] += self._session_cost(s, pricing)

        grand_total = sum(d["tokens"] for d in proj_data.values())

        result = []
        for project, d in proj_data.items():
            pct = (d["tokens"] / grand_total * 100) if grand_total > 0 else 0.0
            result.append(ProjectDistribution(
                project=project,
                total_tokens=d["tokens"],
                session_count=d["sessions"],
                message_count=d["messages"],
                percentage=round(pct, 1),
                cost_usd=round(d["cost"], 4),
            ))
        result.sort(key=lambda x: x.total_tokens, reverse=True)
        return result

    def _compute_daily_trends(
        self,
        sessions: list[SessionTranscript],
        pricing: dict[str, ModelPrice] | None = None,
    ) -> list[DailyTrend]:
        daily: dict[str, dict] = defaultdict(
            lambda: {"tokens": 0, "sessions": 0, "messages": 0, "cost": 0.0}
        )
        for s in sessions:
            if s.start_time is None:
                continue
            date_str = s.start_time.strftime("%Y-%m-%d")
            daily[date_str]["sessions"] += 1
            daily[date_str]["messages"] += len(s.messages)
            daily[date_str]["tokens"] += s.total_tokens.total
            daily[date_str]["cost"] += self._session_cost(s, pricing)

        result = [
            DailyTrend(
                date=date,
                total_tokens=d["tokens"],
                session_count=d["sessions"],
                message_count=d["messages"],
                cost_usd=round(d["cost"], 4),
            )
            for date, d in daily.items()
        ]
        result.sort(key=lambda x: x.date)
        return result

    def _compute_session_overviews(
        self,
        sessions: list[SessionTranscript],
        pricing: dict[str, ModelPrice] | None = None,
    ) -> list[SessionOverview]:
        result = []
        for s in sessions:
            duration = 0.0
            if s.start_time and s.end_time:
                duration = (s.end_time - s.start_time).total_seconds()

            tool_count = sum(len(m.tool_calls) for m in s.messages)
            cost = self._session_cost(s, pricing)

            result.append(SessionOverview(
                session_id=s.session_id,
                project=s.project,
                model=s.model,
                start_time=s.start_time,
                duration_seconds=duration,
                message_count=len(s.messages),
                tool_call_count=tool_count,
                total_tokens=s.total_tokens.total,
                cost_usd=round(cost, 4),
            ))
        result.sort(key=lambda x: x.total_tokens, reverse=True)
        return result

    def _compute_hourly_distribution(
        self, sessions: list[SessionTranscript]
    ) -> list[HourlyDistribution]:
        hours: dict[int, dict] = defaultdict(lambda: {"sessions": 0, "messages": 0})
        seen_session_hours: set[tuple[str, int]] = set()

        for s in sessions:
            for msg in s.messages:
                h = msg.timestamp.hour
                hours[h]["messages"] += 1
                key = (s.session_id, h)
                if key not in seen_session_hours:
                    seen_session_hours.add(key)
                    hours[h]["sessions"] += 1

        result = [
            HourlyDistribution(hour=h, session_count=d["sessions"], message_count=d["messages"])
            for h, d in hours.items()
        ]
        result.sort(key=lambda x: x.hour)
        return result

    def _compute_subagent_distribution(
        self, subagents: list[SubagentTranscript]
    ) -> list[SubagentDistribution]:
        if not subagents:
            return []

        type_data: dict[str, dict] = defaultdict(
            lambda: {"count": 0, "tokens": 0, "messages": 0}
        )
        for sa in subagents:
            type_data[sa.agent_type]["count"] += 1
            type_data[sa.agent_type]["tokens"] += sa.total_tokens.total
            type_data[sa.agent_type]["messages"] += len(sa.messages)

        grand_total = sum(d["tokens"] for d in type_data.values())

        result = []
        for agent_type, d in type_data.items():
            pct = (d["tokens"] / grand_total * 100) if grand_total > 0 else 0.0
            avg = d["tokens"] // d["count"] if d["count"] > 0 else 0
            result.append(SubagentDistribution(
                agent_type=agent_type,
                count=d["count"],
                total_tokens=d["tokens"],
                avg_tokens=avg,
                total_messages=d["messages"],
                percentage=round(pct, 1),
            ))
        result.sort(key=lambda x: x.total_tokens, reverse=True)
        return result

    @staticmethod
    def _session_cost(
        session: SessionTranscript,
        pricing: dict[str, ModelPrice] | None = None,
    ) -> float:
        """Compute total cost for a session by summing per-message costs."""
        total = 0.0
        for msg in session.messages:
            if msg.token_usage and msg.model:
                price = get_model_price(msg.model, pricing)
                total += compute_cost(
                    msg.token_usage.input_tokens,
                    msg.token_usage.output_tokens,
                    msg.token_usage.cache_creation_tokens,
                    msg.token_usage.cache_read_tokens,
                    price,
                )
        return total

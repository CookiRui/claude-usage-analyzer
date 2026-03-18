"""Parser for projects/{project}/{session}.jsonl — full session transcripts."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from claude_usage_analyzer.models import (
    Message,
    ParseWarning,
    SessionTranscript,
    TokenUsage,
)

MAX_CONTENT_PREVIEW = 200


class SessionLogParser:
    def parse(
        self, paths: list[Path]
    ) -> tuple[list[SessionTranscript], list[ParseWarning]]:
        # Collect messages grouped by session_id, also track project per session
        sessions_msgs: dict[str, list[Message]] = defaultdict(list)
        session_project: dict[str, str] = {}
        warnings: list[ParseWarning] = []

        for path in paths:
            project_name = path.parent.name
            self._parse_file(path, project_name, sessions_msgs, session_project, warnings)

        # Build SessionTranscript objects
        sessions: list[SessionTranscript] = []
        for session_id, messages in sessions_msgs.items():
            messages.sort(key=lambda m: m.timestamp)
            total = TokenUsage()
            models: dict[str, int] = defaultdict(int)
            for msg in messages:
                if msg.token_usage:
                    total = total + msg.token_usage
                if msg.model:
                    models[msg.model] += 1

            # Most used model
            primary_model = max(models, key=models.get) if models else None

            sessions.append(SessionTranscript(
                session_id=session_id,
                project=session_project.get(session_id, ""),
                messages=messages,
                total_tokens=total,
                start_time=messages[0].timestamp if messages else None,
                end_time=messages[-1].timestamp if messages else None,
                model=primary_model,
            ))

        return sessions, warnings

    def _parse_file(
        self,
        path: Path,
        project_name: str,
        sessions_msgs: dict[str, list[Message]],
        session_project: dict[str, str],
        warnings: list[ParseWarning],
    ) -> None:
        if not path.is_file():
            warnings.append(ParseWarning(str(path), None, f"File not found: {path}"))
            return

        with open(path, encoding="utf-8", errors="replace") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    warnings.append(ParseWarning(str(path), line_num, f"JSON parse error: {e}"))
                    continue

                msg_type = data.get("type")
                if msg_type not in ("user", "assistant"):
                    continue

                session_id = data.get("sessionId", "")
                session_project[session_id] = project_name

                msg_data = data.get("message", {})
                role = msg_data.get("role", msg_type)

                # Extract content preview
                content = msg_data.get("content", "")
                content_preview = self._extract_content_preview(content)

                # Extract token usage (assistant only)
                token_usage = None
                model = None
                tool_calls: list[str] = []

                if role == "assistant":
                    model = msg_data.get("model")
                    usage = msg_data.get("usage")
                    if usage:
                        token_usage = TokenUsage(
                            input_tokens=usage.get("input_tokens", 0),
                            output_tokens=usage.get("output_tokens", 0),
                            cache_read_tokens=usage.get("cache_read_input_tokens", 0),
                            cache_creation_tokens=usage.get("cache_creation_input_tokens", 0),
                        )

                    # Extract tool calls from content blocks
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "tool_use":
                                name = block.get("name", "")
                                if name:
                                    tool_calls.append(name)

                # Parse timestamp
                ts_str = data.get("timestamp", "")
                try:
                    timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    timestamp = datetime.now(tz=timezone.utc)

                message = Message(
                    role=role,
                    uuid=data.get("uuid", ""),
                    timestamp=timestamp,
                    session_id=session_id,
                    content_preview=content_preview,
                    token_usage=token_usage,
                    model=model,
                    tool_calls=tool_calls,
                )

                sessions_msgs[session_id].append(message)

    @staticmethod
    def _extract_content_preview(content) -> str:
        if isinstance(content, str):
            return content[:MAX_CONTENT_PREVIEW]
        if isinstance(content, list):
            # Find first text block or tool_result
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        return block.get("text", "")[:MAX_CONTENT_PREVIEW]
                    if block.get("type") == "tool_result":
                        return f"[tool_result: {block.get('tool_use_id', '')}]"
            return "[complex content]"
        return ""

"""Parser for subagent logs — agent-{id}.jsonl + agent-{id}.meta.json."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from claude_usage_analyzer.models import (
    Message,
    ParseWarning,
    SubagentFile,
    SubagentTranscript,
    TokenUsage,
)
from claude_usage_analyzer.parsers.session_log import SessionLogParser

# Reuse the content preview extraction
_extract_content_preview = SessionLogParser._extract_content_preview


class SubagentParser:
    def parse(
        self, files: list[SubagentFile]
    ) -> tuple[list[SubagentTranscript], list[ParseWarning]]:
        results: list[SubagentTranscript] = []
        warnings: list[ParseWarning] = []

        for sf in files:
            agent_id = self._extract_agent_id(sf.jsonl_path.stem)
            agent_type, description = self._read_meta(sf.meta_path, warnings)

            messages, file_warnings = self._parse_jsonl(sf.jsonl_path)
            warnings.extend(file_warnings)

            total = TokenUsage()
            models: dict[str, int] = defaultdict(int)
            for msg in messages:
                if msg.token_usage:
                    total = total + msg.token_usage
                if msg.model:
                    models[msg.model] += 1

            primary_model = max(models, key=models.get) if models else None

            results.append(SubagentTranscript(
                agent_id=agent_id,
                session_id=sf.session_id,
                project=sf.project,
                agent_type=agent_type,
                description=description,
                messages=messages,
                total_tokens=total,
                start_time=messages[0].timestamp if messages else None,
                end_time=messages[-1].timestamp if messages else None,
                model=primary_model,
            ))

        return results, warnings

    def _read_meta(
        self, meta_path: Path | None, warnings: list[ParseWarning]
    ) -> tuple[str, str]:
        if meta_path is None:
            return "unknown", ""
        try:
            with open(meta_path, encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            return data.get("agentType", "unknown"), data.get("description", "")
        except (json.JSONDecodeError, OSError) as e:
            warnings.append(ParseWarning(str(meta_path), None, f"Failed to parse meta: {e}"))
            return "unknown", ""

    def _parse_jsonl(
        self, path: Path
    ) -> tuple[list[Message], list[ParseWarning]]:
        messages: list[Message] = []
        warnings: list[ParseWarning] = []

        if not path.is_file():
            warnings.append(ParseWarning(str(path), None, f"File not found: {path}"))
            return messages, warnings

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

                msg_data = data.get("message", {})
                role = msg_data.get("role", msg_type)
                content = msg_data.get("content", "")
                content_preview = _extract_content_preview(content)

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
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "tool_use":
                                name = block.get("name", "")
                                if name:
                                    tool_calls.append(name)

                ts_str = data.get("timestamp", "")
                try:
                    timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    timestamp = datetime.now(tz=timezone.utc)

                session_id = data.get("sessionId", "")

                messages.append(Message(
                    role=role,
                    uuid=data.get("uuid", ""),
                    timestamp=timestamp,
                    session_id=session_id,
                    content_preview=content_preview,
                    token_usage=token_usage,
                    model=model,
                    tool_calls=tool_calls,
                ))

        messages.sort(key=lambda m: m.timestamp)
        return messages, warnings

    @staticmethod
    def _extract_agent_id(stem: str) -> str:
        m = re.match(r"^agent-(.+)$", stem)
        return m.group(1) if m else stem

"""JSON exporter."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from claude_usage_analyzer.exporters import BaseExporter
from claude_usage_analyzer.models import AnalysisResult


class JsonExporter(BaseExporter):
    def export(self, data: AnalysisResult, output: Path) -> None:
        output = Path(output)
        raw = asdict(data)
        # Convert datetime objects to ISO strings
        self._convert_datetimes(raw)
        output.write_text(
            json.dumps(raw, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    def _convert_datetimes(self, obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if hasattr(v, "isoformat"):
                    obj[k] = v.isoformat()
                else:
                    self._convert_datetimes(v)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                if hasattr(v, "isoformat"):
                    obj[i] = v.isoformat()
                else:
                    self._convert_datetimes(v)

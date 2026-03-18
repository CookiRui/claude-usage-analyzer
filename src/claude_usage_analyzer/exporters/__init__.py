"""Exporters package — BaseExporter + factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from claude_usage_analyzer.models import AnalysisResult


class BaseExporter(ABC):
    @abstractmethod
    def export(self, data: AnalysisResult, output: Path) -> None: ...


def get_exporter(fmt: str) -> BaseExporter:
    from claude_usage_analyzer.exporters.csv_exporter import CsvExporter
    from claude_usage_analyzer.exporters.html_exporter import HtmlExporter
    from claude_usage_analyzer.exporters.json_exporter import JsonExporter

    exporters: dict[str, type[BaseExporter]] = {
        "json": JsonExporter,
        "csv": CsvExporter,
        "html": HtmlExporter,
    }
    if fmt not in exporters:
        raise ValueError(f"Unknown export format: {fmt!r}. Supported: {list(exporters)}")
    return exporters[fmt]()


__all__ = ["BaseExporter", "get_exporter"]

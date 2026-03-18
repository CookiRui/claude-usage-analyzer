"""HTML exporter — generates a self-contained HTML report."""

from __future__ import annotations

from pathlib import Path

from claude_usage_analyzer.exporters import BaseExporter
from claude_usage_analyzer.models import AnalysisResult


class HtmlExporter(BaseExporter):
    def export(self, data: AnalysisResult, output: Path) -> None:
        output = Path(output)
        html = self._render(data)
        output.write_text(html, encoding="utf-8")

    def _render(self, data: AnalysisResult) -> str:
        ts = data.token_summary
        period = f"{data.analysis_period[0]} ~ {data.analysis_period[1]}"

        model_rows = "".join(
            f"<tr><td>{m.model}</td><td>{m.input_tokens:,}</td><td>{m.output_tokens:,}</td>"
            f"<td>{m.session_count}</td><td>{m.message_count}</td><td>{m.percentage}%</td></tr>"
            for m in data.model_distribution
        )

        project_rows = "".join(
            f"<tr><td>{p.project}</td><td>{p.total_tokens:,}</td>"
            f"<td>{p.session_count}</td><td>{p.message_count}</td><td>{p.percentage}%</td></tr>"
            for p in data.project_distribution
        )

        daily_rows = "".join(
            f"<tr><td>{d.date}</td><td>{d.total_tokens:,}</td>"
            f"<td>{d.session_count}</td><td>{d.message_count}</td></tr>"
            for d in data.daily_trends
        )

        session_rows = "".join(
            f"<tr><td>{s.session_id[:12]}...</td><td>{s.project}</td>"
            f"<td>{s.model or ''}</td><td>{s.duration_seconds:.0f}s</td>"
            f"<td>{s.message_count}</td><td>{s.tool_call_count}</td>"
            f"<td>{s.total_tokens:,}</td></tr>"
            for s in data.session_overviews[:20]
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Claude Usage Report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         max-width: 960px; margin: 2rem auto; padding: 0 1rem; color: #333; }}
  h1 {{ color: #1a1a2e; }}
  h2 {{ color: #16213e; margin-top: 2rem; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: right; }}
  th {{ background: #f5f5f5; text-align: center; }}
  td:first-child {{ text-align: left; }}
  .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
              gap: 1rem; margin: 1rem 0; }}
  .card {{ background: #f8f9fa; border-radius: 8px; padding: 1rem; text-align: center; }}
  .card .value {{ font-size: 1.8rem; font-weight: bold; color: #1a1a2e; }}
  .card .label {{ font-size: 0.85rem; color: #666; }}
  .period {{ color: #888; font-size: 0.9rem; }}
</style>
</head>
<body>
<h1>Claude Usage Report</h1>
<p class="period">Period: {period} | Sessions: {data.total_sessions} | Messages: {data.total_messages}</p>

<div class="summary">
  <div class="card"><div class="value">{ts.total_input:,}</div><div class="label">Input Tokens</div></div>
  <div class="card"><div class="value">{ts.total_output:,}</div><div class="label">Output Tokens</div></div>
  <div class="card"><div class="value">{ts.total_cache_read:,}</div><div class="label">Cache Read</div></div>
  <div class="card"><div class="value">{ts.total_cache_creation:,}</div><div class="label">Cache Creation</div></div>
  <div class="card"><div class="value">{ts.total_all:,}</div><div class="label">Total Tokens</div></div>
</div>

<h2>Model Distribution</h2>
<table>
<tr><th>Model</th><th>Input</th><th>Output</th><th>Sessions</th><th>Messages</th><th>%</th></tr>
{model_rows}
</table>

<h2>Project Distribution</h2>
<table>
<tr><th>Project</th><th>Total Tokens</th><th>Sessions</th><th>Messages</th><th>%</th></tr>
{project_rows}
</table>

<h2>Daily Trends</h2>
<table>
<tr><th>Date</th><th>Total Tokens</th><th>Sessions</th><th>Messages</th></tr>
{daily_rows}
</table>

<h2>Top Sessions</h2>
<table>
<tr><th>Session</th><th>Project</th><th>Model</th><th>Duration</th><th>Messages</th><th>Tools</th><th>Tokens</th></tr>
{session_rows}
</table>

</body>
</html>"""

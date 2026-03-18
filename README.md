# claude-usage-analyzer

Analyze your [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI usage — track token consumption, session patterns, model distribution, and more.

## Features

- **Session Log Parsing** — Parse full conversation transcripts from `~/.claude/projects/`
- **Subagent Analysis** — Parse and analyze spawned subagent sessions (Explore, Plan, etc.)
- **Token Statistics** — Input, output, cache read, cache creation tokens
- **Multi-Dimension Analysis** — By model, by project, by day, by hour
- **Session Overview** — Duration, message count, tool calls, ranked by token usage
- **Report Export** — JSON, CSV, and self-contained HTML reports
- **Rich Terminal Output** — Beautiful tables with colors via Rich

## Installation

```bash
git clone https://github.com/CookiRui/claude-usage-analyzer.git
cd claude-usage-analyzer
pip install -e .
```

## Usage

```bash
# Analyze all logs (reads ~/.claude by default)
claude-usage analyze

# Only last 7 days
claude-usage analyze --days 7

# Show top 20 sessions
claude-usage analyze --top 20

# Export HTML report
claude-usage export --format html -o report.html

# Export JSON
claude-usage export --format json -o report.json

# Export CSV
claude-usage export --format csv -o report.csv

# Specify custom log directory
claude-usage analyze /path/to/.claude
```

## Example Output

```
Claude Usage Report  (2026-02-24 ~ 2026-03-18)
Sessions: 105  |  Messages: 34090  |  Subagents: 769

          Token Summary
┌────────────────┬────────────────┐
│ Metric         │         Tokens │
├────────────────┼────────────────┤
│ Input          │      1,618,760 │
│ Output         │      5,257,990 │
│ Cache Read     │  1,904,659,750 │
│ Cache Creation │     87,377,494 │
│ Total          │  1,998,913,994 │
└────────────────┴────────────────┘

                Model Distribution
┌───────────────────┬───────────┬───────────┬──────────┬──────────┬───────┐
│ Model             │     Input │    Output │ Sessions │ Messages │     % │
├───────────────────┼───────────┼───────────┼──────────┼──────────┼───────┤
│ claude-opus-4-6   │ 1,592,889 │ 5,180,105 │      101 │    19678 │ 99.4% │
│ claude-sonnet-4-6 │    25,555 │    15,561 │        1 │       31 │  0.6% │
└───────────────────┴───────────┴───────────┴──────────┴──────────┴───────┘
```

## Data Sources

The tool reads from `~/.claude/`:

| Source | Location | Content |
|--------|----------|---------|
| Session Transcripts | `projects/{project}/{session}.jsonl` | Full conversation logs with token usage |
| Subagent Logs | `projects/{project}/{session}/subagents/agent-*.jsonl` | Spawned agent sessions |
| Stats Cache | `stats-cache.json` | Pre-aggregated daily activity |
| Session Metadata | `sessions/{pid}.json` | PID, working directory, start time |
| Command History | `history.jsonl` | User input history |

## Architecture

```
src/claude_usage_analyzer/
  parsers/      # Log file parsing (JSONL/JSON → dataclass)
  analyzers/    # Usage analysis (6 dimensions)
  exporters/    # Report export (JSON/CSV/HTML)
  cli.py        # Click CLI entry point
  models.py     # All data models (dataclass)
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/
```

## License

MIT

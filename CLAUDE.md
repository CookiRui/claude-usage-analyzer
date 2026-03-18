# claude-usage-analyzer

Claude Code CLI 会话日志分析工具。解析日志、统计 token 用量和使用模式、生成报告。

## Architecture

```
src/claude_usage_analyzer/
  parsers/    -> 日志文件解析，将原始日志转为结构化数据
  analyzers/  -> 使用量统计、模式分析、趋势计算
  exporters/  -> 报告导出（JSON / CSV / HTML）
  web/        -> 可选 FastAPI Web 面板
  cli.py      -> Click CLI 入口
scripts/      -> 辅助脚本（persistent-solve, repo-map, lint-feedback）
tests/        -> pytest 测试（unit / integration）
Docs/         -> 设计文档
```

## Tech Stack

- Python 3.10+, Click (CLI), Rich (终端输出)
- FastAPI + Uvicorn (可选 Web UI)
- pytest + Ruff (测试 + 代码检查)

## Workflow

- 任何改动完成后必须 commit 并 push 同步到 GitHub 仓库
- 仓库地址：https://github.com/CookiRui/claude-usage-analyzer

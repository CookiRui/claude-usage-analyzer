# Project Constitution

This file **only defines project-specific, counter-intuitive constraints that AI wouldn't know**.

> **Inclusion criteria**: If you remove a rule, will AI's default behavior produce incorrect code? Yes -> keep it; No -> remove it.

---

## §1: 日志解析必须通过 Parser 层

所有日志文件的读取和解析必须通过 `parsers/` 模块中的 Parser 类完成。业务逻辑（analyzers、exporters、CLI）禁止直接读取或 open 原始日志文件。

```python
# ✅ Correct
from claude_usage_analyzer.parsers import SessionLogParser

parser = SessionLogParser()
sessions = parser.parse(log_path)
analyzer.analyze(sessions)

# ❌ Wrong — 业务逻辑直接读文件
import json
with open(log_path) as f:
    data = json.load(f)
    # 直接在 analyzer 里解析日志格式
```

---

## §2: CLI 和 Web 共享核心逻辑

CLI（Click）和 Web（FastAPI）是两个独立入口，但必须调用 `analyzers/` 和 `exporters/` 中的同一套核心逻辑。禁止在 CLI 或 Web 层重复实现分析/导出逻辑。

- CLI 入口: `cli.py` — 使用 Click
- Web 入口: `web/` — 使用 FastAPI
- 两者都调用 `analyzers/` 和 `exporters/`，不自己做数据处理

```python
# ✅ Correct — CLI 调用共享的 analyzer
@main.command()
def analyze(path):
    sessions = SessionLogParser().parse(path)
    result = UsageAnalyzer().analyze(sessions)
    click.echo(format_result(result))

# ❌ Wrong — CLI 里自己算统计
@main.command()
def analyze(path):
    data = json.load(open(path))
    total_tokens = sum(d["tokens"] for d in data)  # 不应在 CLI 层做
```

---

## §3: 技术栈约束

- **必须用 Ruff**，不用 flake8 / pylint / black
- **必须用 pytest**，不用 unittest
- **必须用 Click**（CLI），不用 argparse / fire
- **Web UI 必须用 FastAPI**，不用 Flask / Django

---

## Governance

This constitution has the highest priority, superseding any `CLAUDE.md` or single-session instructions.

### Enforcement Protocol

The following clauses are non-negotiable:

1. **Skill mandatory loading** — When a task matches a Skill's trigger conditions, the Skill must be loaded and followed.
2. **Subagent constraint inheritance** — Subagents must first read `constitution.md` and relevant Skills before execution. Subagent output must pass `verification` skill before merging.
3. **Confirmation gates cannot be skipped** — Steps marked "must wait for user confirmation" in Commands must not be skipped.
4. **Pre-completion verification** — Before declaring any feature or bug fix "complete", the `verification` skill checklist must be executed.
5. **Violation handling** — If committed code violates the constitution, immediately flag and fix it.

# 日志解析器（Log Parser）技术计划

## 1. Overview

### Goals
- 解析 Claude Code CLI 的 4 种日志数据源，输出统一的结构化数据
- 支持：会话日志（JSONL）、统计缓存（JSON）、会话元数据（JSON）、命令历史（JSONL）
- 容错优先：损坏/不完整记录跳过并警告，不中断解析
- 自动发现 `~/.claude/` 下的所有日志文件

### Non-goals
- 不做分析（Analyzer 的职责）
- 不做导出（Exporter 的职责）
- 不做 Web 展示
- 暂不支持远程/多机器日志收集

## 2. Affected Modules

| 模块 | 操作 | 说明 |
|------|------|------|
| `src/claude_usage_analyzer/parsers/` | 新建 | 所有解析器实现 |
| `src/claude_usage_analyzer/models.py` | 新建 | 数据模型（dataclass） |
| `tests/unit/test_parsers.py` | 新建 | Parser 单元测试 |
| `tests/unit/test_models.py` | 新建 | 数据模型测试 |
| `tests/fixtures/` | 新建 | 测试用的模拟日志文件 |

## 3. Data Model

```python
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

@dataclass
class Message:
    role: str                    # "user" | "assistant"
    uuid: str
    timestamp: datetime
    session_id: str
    content_preview: str         # 截取前 200 字符
    token_usage: TokenUsage | None = None  # 仅 assistant 消息有
    model: str | None = None
    tool_calls: list[str] = field(default_factory=list)  # 工具名称列表

@dataclass
class SessionTranscript:
    session_id: str
    project: str                 # 项目编码名（目录名）
    messages: list[Message] = field(default_factory=list)
    total_tokens: TokenUsage = field(default_factory=TokenUsage)
    start_time: datetime | None = None
    end_time: datetime | None = None
    model: str | None = None     # 主要使用的模型

@dataclass
class SessionMeta:
    pid: int
    session_id: str
    cwd: str
    started_at: datetime

@dataclass
class CommandRecord:
    display: str                 # 用户输入文本
    timestamp: datetime
    project: str
    session_id: str

@dataclass
class DailyActivity:
    date: str                    # "YYYY-MM-DD"
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
    source: str                  # 文件路径
    line: int | None             # 行号（JSONL 文件）
    message: str                 # 警告信息

@dataclass
class ParseResult:
    """所有 Parser 的统一返回容器"""
    sessions: list[SessionTranscript] = field(default_factory=list)
    session_metas: list[SessionMeta] = field(default_factory=list)
    commands: list[CommandRecord] = field(default_factory=list)
    stats: StatsCache | None = None
    warnings: list[ParseWarning] = field(default_factory=list)
```

## 4. Flow Design

### 主流程
```
用户调用 CLI / API
    ↓
LogDiscovery.discover(claude_dir)
    → 扫描 ~/.claude/ 返回各类日志文件路径
    ↓
各 Parser 分别解析:
    SessionLogParser.parse(jsonl_paths) → list[SessionTranscript]
    StatsCacheParser.parse(json_path)   → StatsCache
    SessionMetaParser.parse(json_paths) → list[SessionMeta]
    HistoryParser.parse(jsonl_path)     → list[CommandRecord]
    ↓
汇总为 ParseResult（含 warnings）
    ↓
返回给 Analyzer / CLI
```

### 错误流
```
JSONL 某行 JSON 损坏
    → 记录 ParseWarning（文件名 + 行号 + 错误信息）
    → 跳过该行，继续解析

JSON 文件整体损坏
    → 记录 ParseWarning
    → 返回 None / 空列表

日志目录不存在
    → 抛出 LogDirectoryNotFoundError（这种错误不应静默）
```

## 5. Module Design

### 5.1 `parsers/__init__.py` — 公开接口

```python
def parse_all(claude_dir: Path | str = "~/.claude") -> ParseResult:
    """一键解析所有日志，返回 ParseResult"""

class LogDiscovery:
    """扫描日志目录，发现各类日志文件"""
    def discover(self, claude_dir: Path) -> DiscoveredLogs

class SessionLogParser:
    """解析 projects/{project}/{session}.jsonl"""
    def parse(self, paths: list[Path]) -> tuple[list[SessionTranscript], list[ParseWarning]]

class StatsCacheParser:
    """解析 stats-cache.json"""
    def parse(self, path: Path) -> tuple[StatsCache | None, list[ParseWarning]]

class SessionMetaParser:
    """解析 sessions/{pid}.json"""
    def parse(self, paths: list[Path]) -> tuple[list[SessionMeta], list[ParseWarning]]

class HistoryParser:
    """解析 history.jsonl"""
    def parse(self, path: Path) -> tuple[list[CommandRecord], list[ParseWarning]]
```

### 5.2 `models.py` — 数据模型

所有 dataclass 定义（见第 3 节）。纯数据，无业务逻辑。

### 5.3 `parsers/discovery.py` — 日志发现

```python
@dataclass
class DiscoveredLogs:
    session_logs: list[Path]      # projects/*/*.jsonl
    stats_cache: Path | None      # stats-cache.json
    session_metas: list[Path]     # sessions/*.json
    history: Path | None          # history.jsonl

class LogDiscovery:
    def discover(self, claude_dir: Path) -> DiscoveredLogs
```

### 5.4 `parsers/session_log.py` — 会话日志解析

逐行读取 JSONL，识别 `type` 字段：
- `"user"` / `"assistant"` → Message
- 提取 `costUSD`、`usage` 等 token 字段
- 按 sessionId 分组为 SessionTranscript

### 5.5 `parsers/stats_cache.py` — 统计缓存解析

读取 JSON，映射到 StatsCache dataclass。

### 5.6 `parsers/session_meta.py` — 会话元数据解析

遍历 `sessions/*.json`，映射到 SessionMeta。

### 5.7 `parsers/history.py` — 命令历史解析

逐行读取 JSONL，映射到 CommandRecord。

## 6. Test Plan

每个 Parser 按 TDD RED-GREEN-REFACTOR 开发。测试使用 `tests/fixtures/` 下的模拟日志文件。

| TDD Cycle | 描述 | 测试文件 |
|-----------|------|----------|
| 1 | models.py — 数据模型创建和基本验证 | test_models.py |
| 2 | LogDiscovery — 扫描目录发现日志文件 | test_parsers.py |
| 3 | LogDiscovery — 目录不存在时抛出异常 | test_parsers.py |
| 4 | HistoryParser — 解析正常 JSONL | test_parsers.py |
| 5 | HistoryParser — 损坏行容错 | test_parsers.py |
| 6 | SessionMetaParser — 解析正常 JSON | test_parsers.py |
| 7 | SessionMetaParser — 损坏文件容错 | test_parsers.py |
| 8 | StatsCacheParser — 解析正常 JSON | test_parsers.py |
| 9 | StatsCacheParser — 缺失字段容错 | test_parsers.py |
| 10 | SessionLogParser — 解析 user/assistant 消息 | test_parsers.py |
| 11 | SessionLogParser — 提取 token 用量 | test_parsers.py |
| 12 | SessionLogParser — 按 session 分组 | test_parsers.py |
| 13 | SessionLogParser — 损坏行容错 | test_parsers.py |
| 14 | parse_all — 端到端集成 | test_parsers.py |

## 7. Constitution Compliance Audit

| 条款 | 状态 | 说明 |
|------|------|------|
| §1: Parser 层隔离 | ✅ 合规 | 所有日志读取/解析都在 parsers/ 模块内完成 |
| §2: CLI/Web 共享逻辑 | ✅ 合规 | Parser 返回 ParseResult，CLI 和 Web 都调用同一个 parse_all() |
| §3: 技术栈 | ✅ 合规 | 使用 pytest 测试，Ruff 检查，无违禁依赖 |
| coding-style Rule 1 | ✅ 合规 | 所有输出数据用 dataclass 定义 |
| coding-style Rule 2 | N/A | 本功能不涉及 Exporter |

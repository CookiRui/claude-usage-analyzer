# Subagent 日志解析 — 技术计划

## 1. Overview

### Goals
- 解析 `{session}/subagents/agent-{id}.jsonl` 和 `agent-{id}.meta.json`
- 提取 subagent 类型、描述、token 用量、工具调用、消息数
- 扩展 LogDiscovery 发现 subagent 文件
- 扩展 ParseResult 包含 subagent 数据
- Analyzer 新增 subagent 维度（按 agent 类型聚合统计）
- CLI 新增 subagent 统计表格

### Non-goals
- 不解析 `tool-results/` 目录
- 不做 subagent 的嵌套关系追踪（agent 内再 spawn agent）
- 不修改 Exporter（AnalysisResult 变更后自动包含）

## 2. Affected Modules

| 模块 | 操作 | 说明 |
|------|------|------|
| `models.py` | 修改 | 新增 SubagentTranscript, SubagentDistribution; 扩展 ParseResult, AnalysisResult |
| `parsers/discovery.py` | 修改 | 发现 subagent 文件 |
| `parsers/subagent.py` | 新建 | SubagentParser 实现 |
| `parsers/__init__.py` | 修改 | parse_all 集成 subagent 解析 |
| `analyzers/usage.py` | 修改 | 新增 _compute_subagent_distribution |
| `cli.py` | 修改 | 新增 subagent 统计表格 |
| `tests/fixtures/` | 修改 | 新增 subagent 模拟文件 |
| `tests/unit/test_parsers.py` | 修改 | SubagentParser 测试 |
| `tests/unit/test_analyzers.py` | 修改 | subagent 分析测试 |

## 3. Data Model

```python
@dataclass
class SubagentTranscript:
    agent_id: str              # hex ID (e.g. "a5adee04ff146cd16")
    session_id: str            # 父会话 ID
    project: str               # 项目名
    agent_type: str            # "Explore", "Plan", "general-purpose" 等
    description: str           # agent 任务描述
    messages: list[Message]
    total_tokens: TokenUsage
    start_time: datetime | None
    end_time: datetime | None
    model: str | None

@dataclass
class SubagentDistribution:
    agent_type: str
    count: int                 # 调用次数
    total_tokens: int
    avg_tokens: int
    total_messages: int
    percentage: float
```

扩展 ParseResult:
```python
@dataclass
class ParseResult:
    ...
    subagents: list[SubagentTranscript] = field(default_factory=list)
```

扩展 AnalysisResult:
```python
@dataclass
class AnalysisResult:
    ...
    subagent_distribution: list[SubagentDistribution] = field(default_factory=list)
    total_subagents: int = 0
```

## 4. Flow Design

### 主流程
```
LogDiscovery.discover()
    → 扫描 projects/{project}/{session}/subagents/
    → 收集 agent-*.jsonl + agent-*.meta.json 路径对
    → 加入 DiscoveredLogs.subagent_files

SubagentParser.parse(subagent_files)
    → 读取 meta.json → agent_type + description
    → 复用 SessionLogParser 的消息解析逻辑解析 JSONL
    → 返回 list[SubagentTranscript]

parse_all() 集成 subagent 解析
Analyzer 增加 subagent 维度
CLI 增加 subagent 表格
```

### 错误流
```
meta.json 缺失 → agent_type 设为 "unknown"，记录 warning
JSONL 损坏行 → 跳过并记录 warning（与现有逻辑一致）
```

## 5. Module Design

### 5.1 `parsers/discovery.py` 扩展

```python
@dataclass
class SubagentFile:
    jsonl_path: Path
    meta_path: Path | None  # meta.json 可能缺失
    session_id: str
    project: str

@dataclass
class DiscoveredLogs:
    ...
    subagent_files: list[SubagentFile] = field(default_factory=list)
```

扫描逻辑：遍历 `projects/*/*/subagents/agent-*.jsonl`。

### 5.2 `parsers/subagent.py`

```python
class SubagentParser:
    def parse(self, files: list[SubagentFile]) -> tuple[list[SubagentTranscript], list[ParseWarning]]
```

复用 SessionLogParser._parse_file 的消息解析逻辑（提取为共享函数）。

### 5.3 `analyzers/usage.py` 扩展

```python
def _compute_subagent_distribution(self, subagents: list[SubagentTranscript]) -> list[SubagentDistribution]
```

### 5.4 `cli.py` 扩展

新增 "Subagent Distribution" Rich 表格。

## 6. Test Plan

| TDD Cycle | 描述 |
|-----------|------|
| 1 | SubagentTranscript / SubagentDistribution dataclass |
| 2 | LogDiscovery 发现 subagent 文件 |
| 3 | SubagentParser — 解析 meta.json |
| 4 | SubagentParser — 解析 JSONL 消息和 token |
| 5 | SubagentParser — meta.json 缺失容错 |
| 6 | SubagentParser — JSONL 损坏行容错 |
| 7 | parse_all 集成 subagent |
| 8 | Analyzer — subagent_distribution |
| 9 | Analyzer — 空 subagent 不崩溃 |
| 10 | CLI — analyze 输出包含 subagent 表格 |

## 7. Constitution Compliance Audit

| 条款 | 状态 | 说明 |
|------|------|------|
| §1: Parser 层隔离 | ✅ | SubagentParser 在 parsers/ 中，业务层不直接读文件 |
| §2: CLI/Web 共享逻辑 | ✅ | subagent 分析在 Analyzer 中，CLI 只做展示 |
| §3: 技术栈 | ✅ | 无新依赖 |
| coding-style Rule 1 | ✅ | 新结构用 dataclass |

# Analyzer + Exporter + CLI 串联 — 技术计划

## 1. Overview

### Goals
- Analyzer：基于 ParseResult 计算 6 个分析维度，输出 AnalysisResult
- Exporter：BaseExporter 基类 + JSON/CSV/HTML 三种导出器
- CLI：串联 Parser → Analyzer → Rich 表格输出 / Exporter 文件导出
- 端到端可用：`claude-usage analyze` 在终端看到分析报告，`claude-usage export` 导出文件

### Non-goals
- 不做 Web UI（后续单独规划）
- 不做实时监控
- 不做费用计算（API 价格经常变，不做硬编码）

## 2. Affected Modules

| 模块 | 操作 | 说明 |
|------|------|------|
| `src/claude_usage_analyzer/models.py` | 修改 | 新增 AnalysisResult 等分析结果 dataclass |
| `src/claude_usage_analyzer/analyzers/` | 新建 | 核心分析逻辑 |
| `src/claude_usage_analyzer/exporters/` | 新建 | BaseExporter + 3 种导出器 |
| `src/claude_usage_analyzer/cli.py` | 修改 | 串联完整流程，Rich 表格输出 |
| `tests/unit/test_analyzers.py` | 新建 | Analyzer 单元测试 |
| `tests/unit/test_exporters.py` | 新建 | Exporter 单元测试 |
| `tests/integration/test_cli.py` | 新建 | CLI 集成测试 |

## 3. Data Model

```python
@dataclass
class TokenSummary:
    total_input: int
    total_output: int
    total_cache_read: int
    total_cache_creation: int
    total_all: int

@dataclass
class ModelDistribution:
    model: str
    input_tokens: int
    output_tokens: int
    session_count: int
    message_count: int
    percentage: float  # 占总 token 百分比

@dataclass
class ProjectDistribution:
    project: str
    total_tokens: int
    session_count: int
    message_count: int
    percentage: float

@dataclass
class DailyTrend:
    date: str
    total_tokens: int
    session_count: int
    message_count: int

@dataclass
class SessionOverview:
    session_id: str
    project: str
    model: str | None
    start_time: datetime | None
    duration_seconds: float
    message_count: int
    tool_call_count: int
    total_tokens: int

@dataclass
class HourlyDistribution:
    hour: int  # 0-23
    session_count: int
    message_count: int

@dataclass
class AnalysisResult:
    token_summary: TokenSummary
    model_distribution: list[ModelDistribution]
    project_distribution: list[ProjectDistribution]
    daily_trends: list[DailyTrend]
    session_overviews: list[SessionOverview]
    hourly_distribution: list[HourlyDistribution]
    total_sessions: int
    total_messages: int
    analysis_period: tuple[str, str]  # (start_date, end_date)
```

## 4. Flow Design

### 主流程
```
CLI: claude-usage analyze [--path ~/.claude] [--days 30] [--top 10]
    ↓
parse_all(path) → ParseResult
    ↓
UsageAnalyzer.analyze(parse_result, days=30) → AnalysisResult
    ↓
RichRenderer.render(analysis_result, top=10) → 终端表格输出

CLI: claude-usage export [--path ~/.claude] [--format json] [-o report.json]
    ↓
parse_all(path) → ParseResult
    ↓
UsageAnalyzer.analyze(parse_result) → AnalysisResult
    ↓
JsonExporter/CsvExporter/HtmlExporter.export(analysis_result, output_path)
```

### 错误流
```
ParseResult 为空（无日志）
    → 输出 "No logs found" 提示，退出码 0

分析期间无数据（days 过滤后为空）
    → 输出 "No data in the specified period" 提示
```

## 5. Module Design

### 5.1 `analyzers/__init__.py` — 公开接口

```python
class UsageAnalyzer:
    def analyze(self, data: ParseResult, days: int | None = None) -> AnalysisResult
```

### 5.2 `analyzers/usage.py` — 核心分析

6 个内部方法对应 6 个分析维度：
- `_compute_token_summary(sessions) → TokenSummary`
- `_compute_model_distribution(sessions) → list[ModelDistribution]`
- `_compute_project_distribution(sessions) → list[ProjectDistribution]`
- `_compute_daily_trends(sessions) → list[DailyTrend]`
- `_compute_session_overviews(sessions) → list[SessionOverview]`
- `_compute_hourly_distribution(sessions) → list[HourlyDistribution]`

### 5.3 `exporters/__init__.py` — BaseExporter + 工厂

```python
class BaseExporter(ABC):
    @abstractmethod
    def export(self, data: AnalysisResult, output: Path) -> None: ...

def get_exporter(fmt: str) -> BaseExporter:
    """工厂方法：'json' → JsonExporter, 'csv' → CsvExporter, 'html' → HtmlExporter"""
```

### 5.4 `exporters/json_exporter.py`
将 AnalysisResult 序列化为 JSON。

### 5.5 `exporters/csv_exporter.py`
导出多个 sheet：token_summary、model_distribution、daily_trends 各一个 CSV 文件（或合并到一个多 section CSV）。

### 5.6 `exporters/html_exporter.py`
生成自包含 HTML 报告（内联 CSS，无外部依赖）。

### 5.7 `cli.py` — CLI 串联

```python
@main.command()
@click.argument("path", default="~/.claude")
@click.option("--days", default=None, type=int, help="Only analyze last N days")
@click.option("--top", default=10, type=int, help="Show top N sessions")
def analyze(path, days, top): ...

@main.command()
@click.argument("path", default="~/.claude")
@click.option("--format", "fmt", type=click.Choice(["json", "csv", "html"]), default="json")
@click.option("--output", "-o", default=None)
@click.option("--days", default=None, type=int)
def export(path, fmt, output, days): ...
```

### 5.8 `cli.py` — RichRenderer

```python
class RichRenderer:
    def render(self, result: AnalysisResult, top: int = 10) -> None:
        """用 Rich 打印分析结果到终端"""
```

## 6. Test Plan

| TDD Cycle | 描述 | 测试文件 |
|-----------|------|----------|
| 1 | AnalysisResult 等新 dataclass | test_models.py |
| 2 | UsageAnalyzer — token 汇总 | test_analyzers.py |
| 3 | UsageAnalyzer — 模型分布 | test_analyzers.py |
| 4 | UsageAnalyzer — 项目分布 | test_analyzers.py |
| 5 | UsageAnalyzer — 每日趋势 | test_analyzers.py |
| 6 | UsageAnalyzer — 会话概览 | test_analyzers.py |
| 7 | UsageAnalyzer — 活跃时段 | test_analyzers.py |
| 8 | UsageAnalyzer — days 过滤 | test_analyzers.py |
| 9 | UsageAnalyzer — 空数据处理 | test_analyzers.py |
| 10 | JsonExporter — 导出 JSON | test_exporters.py |
| 11 | CsvExporter — 导出 CSV | test_exporters.py |
| 12 | HtmlExporter — 导出 HTML | test_exporters.py |
| 13 | get_exporter 工厂方法 | test_exporters.py |
| 14 | CLI analyze 命令 | test_cli.py |
| 15 | CLI export 命令 | test_cli.py |

## 7. Constitution Compliance Audit

| 条款 | 状态 | 说明 |
|------|------|------|
| §1: Parser 层隔离 | ✅ | Analyzer 只接收 ParseResult，不直接读日志文件 |
| §2: CLI/Web 共享逻辑 | ✅ | CLI 和未来 Web 都调用同一套 Analyzer + Exporter |
| §3: 技术栈 | ✅ | Click CLI, pytest, Ruff |
| coding-style Rule 1 | ✅ | AnalysisResult 及子结构全用 dataclass |
| coding-style Rule 2 | ✅ | 导出器继承 BaseExporter，不用 if/else 分支 |

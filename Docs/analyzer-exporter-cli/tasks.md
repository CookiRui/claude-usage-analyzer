# Analyzer + Exporter + CLI — 微任务列表

## 数据模型

- [ ] [TDD] 新增 AnalysisResult 等 dataclass -> `models.py` + `tests/unit/test_models.py` | Done: 新 dataclass 可 import 且测试通过

## Analyzer

- [ ] [TDD] UsageAnalyzer — token 汇总 -> `analyzers/usage.py` + `tests/unit/test_analyzers.py` | Done: TokenSummary 数值正确
- [ ] [TDD] UsageAnalyzer — 模型分布 -> `analyzers/usage.py` + `tests/unit/test_analyzers.py` | Done: 按模型聚合 + percentage 正确
- [ ] [TDD] UsageAnalyzer — 项目分布 -> `analyzers/usage.py` + `tests/unit/test_analyzers.py` | Done: 按项目聚合正确
- [ ] [TDD] UsageAnalyzer — 每日趋势 -> `analyzers/usage.py` + `tests/unit/test_analyzers.py` | Done: 按日期聚合正确
- [ ] [TDD] UsageAnalyzer — 会话概览 -> `analyzers/usage.py` + `tests/unit/test_analyzers.py` | Done: 时长/消息数/工具调用正确
- [ ] [TDD] UsageAnalyzer — 活跃时段 -> `analyzers/usage.py` + `tests/unit/test_analyzers.py` | Done: 24 小时分布正确
- [ ] [TDD] UsageAnalyzer — days 过滤 -> `analyzers/usage.py` + `tests/unit/test_analyzers.py` | Done: 过滤后数据正确
- [ ] [TDD] UsageAnalyzer — 空数据处理 -> `analyzers/usage.py` + `tests/unit/test_analyzers.py` | Done: 空 ParseResult 不崩溃
- [ ] 更新 analyzers/__init__.py 公开接口 -> `analyzers/__init__.py` | Done: UsageAnalyzer 可 import

## Exporter

- [ ] [TDD] BaseExporter 基类 + get_exporter 工厂 -> `exporters/__init__.py` + `tests/unit/test_exporters.py` | Done: 工厂返回正确类型
- [ ] [TDD] JsonExporter -> `exporters/json_exporter.py` + `tests/unit/test_exporters.py` | Done: 输出合法 JSON
- [ ] [TDD] CsvExporter -> `exporters/csv_exporter.py` + `tests/unit/test_exporters.py` | Done: 输出合法 CSV
- [ ] [TDD] HtmlExporter -> `exporters/html_exporter.py` + `tests/unit/test_exporters.py` | Done: 输出自包含 HTML

## CLI 串联

- [ ] [TDD] cli.py analyze 命令 — 串联 Parser→Analyzer→Rich 输出 -> `cli.py` + `tests/integration/test_cli.py` | Done: CliRunner 输出包含表格数据
- [ ] [TDD] cli.py export 命令 — 串联 Parser→Analyzer→Exporter -> `cli.py` + `tests/integration/test_cli.py` | Done: 生成文件且内容正确
- [ ] RichRenderer — 终端表格渲染 -> `cli.py` | Done: 各分析维度有对应表格输出

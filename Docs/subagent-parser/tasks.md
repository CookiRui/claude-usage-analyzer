# Subagent 日志解析 — 微任务列表

## Fixtures

- [ ] 创建 subagent 测试 fixture 文件 -> `tests/fixtures/projects/test-project/session-001/subagents/` | Done: agent-*.jsonl + agent-*.meta.json 存在

## 数据模型

- [ ] [TDD] 新增 SubagentTranscript / SubagentDistribution / SubagentFile dataclass -> `models.py` + `tests/unit/test_models.py` | Done: 可 import 且测试通过
- [ ] 扩展 ParseResult 增加 subagents 字段 -> `models.py` | Done: ParseResult.subagents 可用
- [ ] 扩展 AnalysisResult 增加 subagent_distribution + total_subagents -> `models.py` | Done: 字段可用

## Parser

- [ ] [TDD] LogDiscovery 发现 subagent 文件 -> `parsers/discovery.py` + `tests/unit/test_parsers.py` | Done: DiscoveredLogs.subagent_files 包含 fixture 文件
- [ ] [TDD] SubagentParser — 解析 meta.json -> `parsers/subagent.py` + `tests/unit/test_parsers.py` | Done: agent_type + description 正确
- [ ] [TDD] SubagentParser — 解析 JSONL 消息和 token -> `parsers/subagent.py` + `tests/unit/test_parsers.py` | Done: messages + total_tokens 正确
- [ ] [TDD] SubagentParser — meta.json 缺失容错 -> `parsers/subagent.py` + `tests/unit/test_parsers.py` | Done: agent_type="unknown" + warning
- [ ] [TDD] SubagentParser — JSONL 损坏行容错 -> `parsers/subagent.py` + `tests/unit/test_parsers.py` | Done: 跳过损坏行 + warning
- [ ] 集成 parse_all -> `parsers/__init__.py` + `tests/unit/test_parsers.py` | Done: ParseResult.subagents 有数据

## Analyzer

- [ ] [TDD] UsageAnalyzer — subagent_distribution -> `analyzers/usage.py` + `tests/unit/test_analyzers.py` | Done: 按 agent_type 聚合正确
- [ ] [TDD] UsageAnalyzer — 空 subagent 不崩溃 -> `tests/unit/test_analyzers.py` | Done: 空列表正常

## CLI

- [ ] [TDD] cli.py analyze — subagent 统计表格 -> `cli.py` + `tests/integration/test_cli.py` | Done: 输出包含 "Subagent" 表格

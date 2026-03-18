# 日志解析器 — 微任务列表

## 准备阶段

- [ ] 创建测试 fixtures 目录和模拟日志文件 -> `tests/fixtures/` | Done: fixtures 目录存在且包含各类模拟日志
- [ ] 创建数据模型 -> `src/claude_usage_analyzer/models.py` | Done: 所有 dataclass 可 import

## 数据模型

- [ ] [TDD] 实现 TokenUsage / Message / SessionTranscript dataclass -> `models.py` + `tests/unit/test_models.py` | Done: test_models.py 测试通过
- [ ] [TDD] 实现 SessionMeta / CommandRecord dataclass -> `models.py` + `tests/unit/test_models.py` | Done: 测试通过
- [ ] [TDD] 实现 StatsCache / DailyActivity / ModelTokenStats dataclass -> `models.py` + `tests/unit/test_models.py` | Done: 测试通过
- [ ] [TDD] 实现 ParseResult / ParseWarning dataclass -> `models.py` + `tests/unit/test_models.py` | Done: 测试通过

## LogDiscovery

- [ ] [TDD] LogDiscovery.discover — 扫描正常目录返回 DiscoveredLogs -> `parsers/discovery.py` + `tests/unit/test_parsers.py` | Done: 发现 fixture 中所有日志文件
- [ ] [TDD] LogDiscovery.discover — 目录不存在抛 LogDirectoryNotFoundError -> `parsers/discovery.py` + `tests/unit/test_parsers.py` | Done: 异常测试通过

## HistoryParser

- [ ] [TDD] HistoryParser.parse — 解析正常 JSONL 行 -> `parsers/history.py` + `tests/unit/test_parsers.py` | Done: 返回 CommandRecord 列表
- [ ] [TDD] HistoryParser.parse — 损坏行跳过并返回 warning -> `parsers/history.py` + `tests/unit/test_parsers.py` | Done: warnings 包含损坏行信息

## SessionMetaParser

- [ ] [TDD] SessionMetaParser.parse — 解析正常 JSON -> `parsers/session_meta.py` + `tests/unit/test_parsers.py` | Done: 返回 SessionMeta 列表
- [ ] [TDD] SessionMetaParser.parse — 损坏文件跳过并返回 warning -> `parsers/session_meta.py` + `tests/unit/test_parsers.py` | Done: warnings 正确

## StatsCacheParser

- [ ] [TDD] StatsCacheParser.parse — 解析正常 stats-cache.json -> `parsers/stats_cache.py` + `tests/unit/test_parsers.py` | Done: 返回 StatsCache 对象
- [ ] [TDD] StatsCacheParser.parse — 缺失字段容错 -> `parsers/stats_cache.py` + `tests/unit/test_parsers.py` | Done: 缺失字段用默认值，返回 warning

## SessionLogParser（核心，最复杂）

- [ ] [TDD] SessionLogParser — 解析 user 消息 -> `parsers/session_log.py` + `tests/unit/test_parsers.py` | Done: 提取 role/uuid/timestamp/content
- [ ] [TDD] SessionLogParser — 解析 assistant 消息 + token 用量 -> `parsers/session_log.py` + `tests/unit/test_parsers.py` | Done: 提取 TokenUsage
- [ ] [TDD] SessionLogParser — 提取工具调用名称 -> `parsers/session_log.py` + `tests/unit/test_parsers.py` | Done: tool_calls 列表正确
- [ ] [TDD] SessionLogParser — 按 sessionId 分组为 SessionTranscript -> `parsers/session_log.py` + `tests/unit/test_parsers.py` | Done: 多 session 正确分组
- [ ] [TDD] SessionLogParser — 损坏行容错 -> `parsers/session_log.py` + `tests/unit/test_parsers.py` | Done: 跳过损坏行，warnings 正确

## 集成

- [ ] [TDD] parse_all() — 端到端集成测试 -> `parsers/__init__.py` + `tests/unit/test_parsers.py` | Done: 返回完整 ParseResult
- [ ] 更新 parsers/__init__.py 公开接口 -> `parsers/__init__.py` | Done: parse_all / 各 Parser 类可 import

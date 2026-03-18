# Coding Style Rules

> Supplements the constitution with details it can't cover. If derivable from the constitution, delete it.

## Rule 1: 数据容器用 dataclass 或 TypedDict (per Constitution §1)

Parser 输出的结构化数据必须使用 `dataclass` 或 `TypedDict` 定义，不用裸 dict。这样 analyzer 和 exporter 能获得类型提示。

```python
# ✅ Correct
from dataclasses import dataclass

@dataclass
class SessionRecord:
    session_id: str
    start_time: datetime
    total_tokens: int
    model: str

# ❌ Wrong
session = {"id": "abc", "tokens": 123}  # 裸 dict 无类型保障
```

**Exceptions:** 临时的中间变量或测试数据可以用 dict。

## Rule 2: 导出格式通过 Exporter 基类扩展 (per Constitution §2)

新增导出格式时，继承 `BaseExporter` 并实现 `export()` 方法，不要在现有 exporter 里加 if/else 分支。

```python
# ✅ Correct
class HtmlExporter(BaseExporter):
    def export(self, data: AnalysisResult, output: Path) -> None:
        ...

# ❌ Wrong
def export(data, fmt, output):
    if fmt == "json": ...
    elif fmt == "csv": ...
    elif fmt == "html": ...  # 每加一种格式就多一个分支
```

**Exceptions:** 无。

## Self-check Checklist

- [ ] Parser 输出类型是否用了 dataclass / TypedDict
- [ ] 新代码是否直接 open 了日志文件（应通过 Parser）
- [ ] CLI / Web 层是否包含分析逻辑（应在 analyzers/ 中）
- [ ] 新导出格式是否继承了 BaseExporter

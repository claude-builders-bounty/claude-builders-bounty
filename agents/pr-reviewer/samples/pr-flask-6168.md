## 评审

**PR**：drop support for Python 3.10

### 改动概述

这个 PR 改了 12 个文件，+67 / -433 行，主要集中在 .github, CHANGES.rst, docs, pyproject.toml。改动量最大的是 `uv.lock`, `tests/test_appctx.py`, `pyproject.toml`。 本次带上了测试改动。

### 风险

- 没有检出声明的风险模式（不代表没有风险，只说明没命中已知模式）。

### 改进建议

- 没有发现需要阻断的问题；保持改动聚焦即可。

### 置信度

**High**

---

<sub>由 claude-review 生成：确定性分析来自真实 diff；摘要由模型润色（如配置了 key）。</sub>

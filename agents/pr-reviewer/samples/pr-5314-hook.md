## 评审

**PR**：feat(hook): block destructive bash commands before execution

### 改动概述

这个 PR 改了 5 个文件，+502 / -0 行，主要集中在 hooks。改动量最大的是 `hooks/block-dangerous/block_dangerous.py`, `hooks/block-dangerous/tests/test_hook.py`, `hooks/block-dangerous/install.py`。 本次带上了测试改动。

### 风险

- 没有检出声明的风险模式（不代表没有风险，只说明没命中已知模式）。

### 改进建议

- 没有发现需要阻断的问题；保持改动聚焦即可。

### 置信度

**Medium**

> 置信度不高时会说明原因：命中了高危模式，或改动面过大，需要人再看一遍。

---

<sub>由 claude-review 生成：确定性分析来自真实 diff；摘要由模型润色（如配置了 key）。</sub>

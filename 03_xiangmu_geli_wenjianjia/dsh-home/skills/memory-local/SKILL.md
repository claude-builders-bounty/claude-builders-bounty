---
name: memory-local
version: "1.0.0"
description: Use when you need local vector memory with Ollama bge-m3.
author: Hermes Agent
tags: [memory, vector, ollama, chromadb, bge-m3, auto-context, compression]
requires:
  - python: ">=3.10"
  - pip: ["chromadb>=1.5", "ollama>=0.4"]
---

# Memory-Local: 本地向量记忆技能

## 设计目标
- **零手动触发**：对话开始自动注入相关记忆，结束自动写入
- **语义检索而非关键词**：bge-m3 1024维向量 + Chroma HNSW 索引
- **自动压缩**：长对话自动摘要存储，防上下文爆炸
- **跨会话持久**：Chromadb 本地 SQLite，重启不丢
- **完全本地**：数据不出 D:\Ai\Ollama\Memory

## 架构
```
Hermes Hook (session_start) 
    → query_chroma(user_input) → top-k 记忆注入 system prompt
    
Hermes Hook (session_end / turn_end)
    → extract_facts(assistant+user) → embed(bge-m3) → upsert_chroma
    
Background (可选 cron)
    → compress_old_memories() → summary → replace_raw
```

## 文件结构
```
~/.hermes/skills/memory-local/
├── SKILL.md
├── scripts/
│   ├── memory_core.py      # 核心类：MemoryStore
│   ├── hooks.py            # Hermes hook 入口
│   └── compress.py         # 压缩/摘要逻辑
├── config.yaml             # 可配置参数
└── templates/
    └── system_prompt_injection.md
```

---

## 快速开始
1. 确保 Ollama 服务运行（默认 localhost:11434），已拉取 `bge-m3`
2. 技能加载后自动初始化 ChromaDB 到 `D:/Ai/Ollama/Memory/chroma/`
3. 无需任何手动配置即可工作

---

## 核心 API (供其它 skill/脚本调用)

```python
from memory_local import MemoryStore

mem = MemoryStore()  # 单例，自动初始化

# 写入记忆（自动嵌入+去重）
mem.add(content="用户偏好深色模式", metadata={"type": "preference", "source": "chat"})

# 语义检索
results = mem.search(query="用户喜欢什么主题", top_k=5, min_score=0.35)

# 删除/更新
mem.delete(ids=[...])
mem.update(id=..., new_content=..., new_metadata=...)

# 压缩旧记忆（保留摘要）
mem.compress_older_than(days=30, keep_raw_days=7)
```

---

## 配置 (config.yaml)
```yaml
ollama:
  host: "http://localhost:11434"
  embed_model: "bge-m3"
  timeout: 30

chroma:
  persist_dir: "D:/Ai/Ollama/Memory/chroma"
  collection: "hermes_memory"
  hnsw_space: "cosine"

retrieval:
  top_k: 5
  min_score: 0.35
  max_context_chars: 3000

compression:
  enabled: true
  trigger_turns: 20
  summary_model: "qwen2.5:7b-instruct-q3_K_M"
  keep_raw_days: 7
  summary_max_chars: 500

hooks:
  auto_inject_on_start: true
  auto_save_on_end: true
  save_every_n_turns: 5
```

---

## Hook 集成 (自动生效 - Gateway Hook)

**已创建**：`~/.hermes/hooks/memory-local/` (HOOK.yaml + handler.py)

自动监听事件：
- `session:start` → `on_session_start()` 注入相关记忆到上下文
- `agent:end` → `on_turn_end()` 每轮对话结束提取事实并缓存
- `session:end` → `on_session_end()` 会话结束刷新所有待写入记忆

**启用方式**：确保 Hermes gateway 运行 (`hermes gateway start`)，hook 会自动发现加载。

---

## Cron 定时压缩 (自动生效)

**已创建**：`cronjob: memory-local-compression` (job_id: 7cd551900fe3)

- **时间**：每天凌晨 3:00
- **动作**：压缩超过 7 天的原始 fact 记忆为摘要
- **模型**：qwen2.5:7b-instruct-q3_K_M (需本地已拉取)
- **交付**：本地保存 (deliver=local)

**启用方式**：确保 Hermes gateway 运行，cron 会自动执行。

---

## Cron 定时压缩 (自动生效)

**已创建**：`cronjob: memory-local-compression` (job_id: 7cd551900fe3)

- **时间**：每天凌晨 3:00
- **动作**：压缩超过 7 天的原始 fact 记忆为摘要
- **模型**：qwen2.5:7b-instruct-q3_K_M (需本地已拉取)
- **交付**：本地保存 (deliver=local)

**启用方式**：确保 Hermes gateway 运行，cron 会自动执行。

---

## 进阶用法

### 手动检索注入到当前上下文
```bash
hermes skill run memory-local search "用户的编程语言偏好"
```

### 查看统计
```bash
hermes skill run memory-local stats
```

### 强制压缩
```bash
hermes skill run memory-local compress
```

---

## 故障排查
| 现象 | 原因 | 解决 |
|------|------|------|
| 连接 Ollama 失败 | 服务未启动 | `ollama.exe serve` 或重启托盘应用 |
| Chroma 初始化报错 | 目录权限/路径 | 检查 `D:/Ai/Ollama/Memory/chroma` 可写 |
| 检索结果为空 | 阈值过高/数据太少 | 降低 `min_score` 或多聊几轮 |
| 上下文仍爆炸 | 压缩未生效 | 检查 `compression.enabled: true` 且有摘要模型 |

---

## 更新日志
- v1.0.0: 初始版本，完整自动化流程
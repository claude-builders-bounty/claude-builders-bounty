# Memory-Local System Prompt Injection Template

This template is used by the hook to format retrieved memories for injection into the system prompt.

## Injection Format

```
=== RELEVANT MEMORIES (auto-injected) ===
- [fact] 用户偏好深色模式，不喜欢亮色主题 (score: 0.89)
- [preference] 用户习惯用 Python 做数据分析，不常用 R (score: 0.82)
- [summary] 2024-01会话摘要：用户配置了本地Ollama+bge-m3+ChromaDB记忆系统 (score: 0.76)
=== END MEMORIES ===
```

## Usage in Hook

```python
from memory_local.scripts.hooks import on_session_start

# 在 session_start 时调用
injected_block = on_session_start(session_id="abc123", user_input="帮我写个Python脚本")

# 将 injected_block 预置到 system prompt 或作为第一条 user message 发送
```

## Configuration Controls

| Config | Description |
|--------|-------------|
| `retrieval.top_k` | 最大检索条数 (default: 5) |
| `retrieval.min_score` | 最小相似度阈值 (default: 0.35) |
| `retrieval.max_context_chars` | 注入块最大字符数 (default: 3000) |
| `hooks.auto_inject_on_start` | 是否自动注入 (default: true) |

## Customization

To customize the injection format, modify `MemoryStore.inject_relevant_memories()` in `scripts/memory_core.py`.
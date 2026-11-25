# dsh-memory-local — 跨会话向量记忆（本地）

给 DeepSeek Harness 加真正的语义记忆：每轮对话自动落盘，下次对话自动召回注入。

## 它做什么
- **写入**：每个 turn 结束，把「用户提问 + 助手回答」拼成一条，用 Ollama `bge-m3` 嵌入成 1024 维向量，追加到本地 JSONL。
- **召回**：每个 turn 开始前，用当前用户消息做向量检索（余弦相似度），命中片段以 `<memory-recall>` 块注入系统提示。
- **工具**：`memory_search`（语义检索）、`memory_write`（显式写入事实）、`memory_stats`（条数/路径）。
- **去重**：同一文本（规范化后）不会重复入库。

## 依赖
- Ollama 服务（默认 `http://127.0.0.1:11434`），已安装 `bge-m3`。
- 不依赖任何 npm 包，纯 Node 内置模块。

## 文件
- 记忆库：`$DSH_HOME/memory/memories.jsonl`（每行一条，含 base64 的 float32 向量）
- 加载日志：`$DSH_HOME/memory/plugin.log`（每次挂载写一行，用来确认插件真的起来了）
- 源码：`$DSH_HOME/plugins/dsh-memory-local/`

## 配置（profile 的 cordis.patch.yml）
```yaml
- insert:
    - id: memory-local
      name: '@local/dsh-memory-local'
      config:
        k: 4                 # 每次召回条数
        minScore: 0.45       # 余弦阈值，低于此分不注入
        ollamaUrl: 'http://127.0.0.1:11434'
        embedModel: 'bge-m3'
        maxTextChars: 2000   # 单条记忆最长字符
```

## 验证
1. 重启 DSH 后看 `$DSH_HOME/memory/plugin.log` 是否多出一行 `loaded tools=...`。
2. 新会话里问一句「我的收款偏好是什么」之类曾经聊过的内容，回答里应体现历史信息。
3. 会话工具列表里应出现 `memory_search` / `memory_write` / `memory_stats`。

## 回滚
删掉 profile patch 里的 `- insert: ... memory-local` 这段，重启即可；记忆文件可保留。

## 捕获规则
- 每个 turn 结束，用「最后一条真实用户消息 + 本轮全部 assistant text 段」组成一条记忆。
- 自动跳过运行时上下文、system-reminder、技能目录、父代理指令等"伪用户消息"。
- assistant 只取 `type: "text"` 段，reasoning 不进记忆。
- cwd 从运行时上下文里的 `Current working directory` 提取（拿不到就留空）。

## 调试
config 里加 `debug: true` 会写 `$DSH_HOME/memory/debug.log`（默认关闭）。

## 已知限制
- 召回发生在每个 turn 的第一步，同一 turn 内不重复检索。
- 记忆是原始「问答对」，不做 LLM 蒸馏；条数上限 5000，超出滚动淘汰最旧的。
- 检索是暴力余弦，不做 rerank；相似度阈值 0.45，低于该分不注入。

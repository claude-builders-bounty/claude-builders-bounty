# claude-review — Claude Code PR 审查子代理

输入一个 PR，输出结构化 Markdown 审查意见：变更摘要、风险清单、改进建议、置信度。

## 要求

- Python 3.9+
- GitHub CLI（`gh`）已登录（用于拉取 PR 元数据与 diff）
- 可选：`codex` CLI 或 `claude` CLI（`--backend codex|claude` 时启用 LLM 语义审查）

## 用法

```bash
# 启发式审查（默认，无外部依赖）
python3 claude_review.py --pr https://github.com/owner/repo/pull/123

# LLM 语义审查（需要 codex CLI）
python3 claude_review.py --pr owner/repo/pull/123 --backend codex

# JSON 输出
python3 claude_review.py --pr owner/repo/pull/123 --json
```

## 输出结构

```markdown
## Summary of changes   （2-3 句）
## Identified risks     （清单）
## Improvement suggestions（清单）
## Confidence score: Low / Medium / High
```

## 验证（2 个真实 PR 示例）

见 `samples/`：对两个公开 GitHub PR 运行 `--backend heuristic` 的输出。

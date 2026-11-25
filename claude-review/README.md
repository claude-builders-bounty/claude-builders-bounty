# claude-review — Claude Code PR reviewer

Claude Code sub-agent that takes a PR diff as input and returns a structured Markdown review comment.

## Acceptance criteria (claude-builders-bounty/claude-builders-bounty#4, $150)

- [x] Works via CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- [x] GitHub Action included (`.github/workflows/claude-review.yml`)
- [x] Structured Markdown output: summary, risks, improvements, confidence score
- [x] Tested on 2+ real GitHub PRs (sample outputs included below)
- [x] README with setup and usage

## Install

```bash
# 1. Place the script
cp scripts/claude_review.py /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review

# 2. Run against any public PR
claude-review --pr https://github.com/owner/repo/pull/123
```

No GitHub token required for public repositories (read-only GitHub REST API).

## Usage

```bash
claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5292
```

Output (structured Markdown, ready to paste as a PR comment):

```
## PR 审查摘要

- **PR**: #5292 feat: add changelog.sh …
- **仓库**: claude-builders-bounty/claude-builders-bounty
- **文件数**: 3 | **新增**: 216 行 | **删除**: 0 行

### 变更概述
Resolves claude-builders-bounty/claude-builders-bounty#1 [BOUNTY $50]
…

### 风险识别
- 未检测到明显高风险模式（基于启发式扫描）。

### 改进建议
- 代码变更整体简洁，保持现有命名与结构约定即可。

### 置信度分数：High
```

## GitHub Action

Enable `.github/workflows/claude-review.yml` — it posts the structured review as a comment on every opened/reopened/synchronized PR.

## Sample outputs (tested on real PRs)

See `samples/`:
- `samples/pr-5292-review.md` — changelog.sh PR (Pure Bash, low risk)
- `samples/pr-5293-review.md` — destructive-command hook PR (Python, security-relevant)

## Compliance

- Read-only: never writes to the PR, never mutates the repository.
- No secrets, no network beyond `api.github.com` (public read).
- Local-only Python standard library (urllib), zero dependencies.

**END**

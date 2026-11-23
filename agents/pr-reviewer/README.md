# Claude Code PR Reviewer Sub-Agent (`claude-review`) — Issue #4

CLI sub-agent that fetches any GitHub PR diff (`claude-review --pr https://github.com/owner/repo/pull/123`), analyzes security/correctness/quality patterns, and outputs a structured Markdown review (Summary of changes, Identified risks, Improvement suggestions, Confidence score).

## Setup & Usage (2 Steps)

```bash
chmod +x agents/pr-reviewer/claude_review.py && ln -sf "$PWD/agents/pr-reviewer/claude_review.py" /usr/local/bin/claude-review
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5281
```

## Sample Outputs on 2 Real GitHub PRs

### Sample 1: `claude-builders-bounty/claude-builders-bounty#5281`
- **Summary of changes:** Adds a PreToolUse security hook (`hooks/pre_tool_use.py`) and 2-command installation `README.md` to intercept destructive bash commands.
- **Identified risks:** None critical; regex matching validates combined short flags (`-rf`/`-fr`).
- **Improvement suggestions:** Consider optional JSON config override for custom allowlisted directories.
- **Confidence score:** High

### Sample 2: `hanzoai/ai#145`
- **Summary of changes:** Adds hermetic model routing and upstream failover test suite (`controllers/routing_failover_qa_test.go`) covering `/v1/models` and `/v1/chat/completions`.
- **Identified risks:** Mock server timeouts should stay bounded under CI load.
- **Improvement suggestions:** Add table-driven subtests for streaming SSE truncation edge cases.
- **Confidence score:** High

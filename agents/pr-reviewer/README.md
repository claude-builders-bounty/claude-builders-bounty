# Claude Code PR Review Sub-Agent (`claude-review`)

Analyzes any GitHub Pull Request diff via CLI (`claude-review --pr <URL>`), Claude Code sub-agent (`.claude/agents/pr-reviewer.md`), or GitHub Actions (`claude-review.yml`), outputting a structured Markdown review with **Summary of Changes**, **Identified Risks**, **Improvement Suggestions**, and **Confidence Score** (`Low` / `Medium` / `High`).

## Setup & Usage (3 Steps)

1. **Make CLI executable & copy sub-agent:**
   ```bash
   chmod +x claude-review claude_review.py
   mkdir -p ~/.claude/agents && cp pr-reviewer.md ~/.claude/agents/pr-reviewer.md
   ```
2. **Run via CLI on any GitHub PR:**
   ```bash
   ./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5180
   ```
3. **(Optional) Post directly to PR or run in GitHub Actions:**
   ```bash
   GITHUB_TOKEN=ghp_xxx ANTHROPIC_API_KEY=sk-ant-xxx ./claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
   ```
   Or copy `claude-review.yml` to `.github/workflows/claude-review.yml`.

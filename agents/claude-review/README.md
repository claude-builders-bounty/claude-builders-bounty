# Automated PR Review Agent (`claude-review`)

Fetches any GitHub Pull Request diff and outputs a structured Markdown review containing a 2–3 sentence summary, identified risks, actionable improvement suggestions, and a confidence score (`Low` / `Medium` / `High`).

## Setup & Usage

1. Optional: export your Anthropic key (`export ANTHROPIC_API_KEY=sk-ant-...`) to use `claude-sonnet-4-20250514`, or run with no key for deterministic static diff risk analysis.
2. Review any public or authenticated GitHub PR via CLI:
   ```bash
   python claude_review.py --pr https://github.com/owner/repo/pull/123
   ```
3. Or copy `claude-review-action.yml` into `.github/workflows/claude-review.yml` to comment automatically on every Pull Request.

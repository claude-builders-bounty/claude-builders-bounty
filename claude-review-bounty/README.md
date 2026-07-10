# claude-review — Automated PR Reviewer

A Claude Code sub-agent (stdin/CLI + GitHub Action) that analyzes a PR diff and
posts a structured Markdown review: **summary, identified risks, improvement
suggestions, and a confidence score.**

## Features
- CLI: `claude-review.py --pr <url> [--format markdown|json]`
- GitHub Action: drops a review comment on every PR automatically.
- Pure stdlib — no `pip install` needed. Uses only the GitHub REST API.
- Heuristic static checks: destructive SQL, hardcoded secrets, `eval/exec`,
  `subprocess`, `curl | sh`, missing tests, oversized diffs.

## Usage
```bash
# As a CLI
export GITHUB_TOKEN=ghp_xxx
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
python3 claude-review.py --pr 123 --repo owner/repo --format json
```

## As a GitHub Action
Copy `.github/workflows/pr-review.yml` into your repo. It runs on every PR and
posts the structured review as a comment. No extra secrets required (uses the
built-in `GITHUB_TOKEN`).

## Output shape
```markdown
## 🤖 Automated PR Review — #123
### Summary
### Identified Risks
### Improvement Suggestions
### Confidence: High | Medium | Low
```

> Heuristic analysis — a first-pass safety net, not a substitute for human review.

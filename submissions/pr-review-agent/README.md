# Claude Code PR Review Agent

Automated PR review that analyzes diffs for security, logic, and style issues.

## Setup (3 steps)

1. Copy `SKILL.md` to `.claude/skills/`
2. Make script executable: `chmod +x scripts/review-pr.py`
3. Run: `claude-review --pr https://github.com/owner/repo/pull/123` (or `/review-pr` in Claude Code)

## What it detects

| Category | Checks |
|----------|--------|
| 🔴 Security | API keys, tokens, secrets, eval(), os.system(), shell=True |
| 🟡 Injection | SQL injection, XSS, path traversal |
| 🟢 Logic | Empty catch blocks, unhandled rejections, TODO/FIXME |

## Usage

```bash
# Review a PR
python scripts/review-pr.py --pr https://github.com/owner/repo/pull/123

# Review and post comment
python scripts/review-pr.py --pr https://github.com/owner/repo/pull/123 --post
```

## Sample

Tested on real PRs — see sample-output.md for examples.

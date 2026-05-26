# Claude Code PR Reviewer Agent

> 💰 **Bounty #4: $150** — PR review sub-agent

Reviews GitHub PRs via CLI and outputs structured Markdown reviews.

## Installation

```bash
chmod +x claude-review
cp claude-review /usr/local/bin/  # or anywhere in PATH
```

Requires `gh` CLI (install via `brew install gh` or https://cli.github.com/).

## Usage

```bash
# Via PR URL
claude-review --pr https://github.com/owner/repo/pull/123

# Via args
claude-review owner repo 123

# JSON output
claude-review --pr https://github.com/owner/repo/pull/123 --output json
```

## Sample Outputs

### PR #1: Feature addition
```
🤖 AI Code Review — vercel/next.js#50001

Review Date: 2026-05-22
Confidence Score: Medium

📋 Summary
This PR modifies 3 files (src/compiler.ts, test/compiler.test.ts, docs/api.md), 
adding 145 lines and removing 12 lines. The changes primarily introduce new 
functionality.

📊 Diff Stats
| Metric | Value |
|--------|-------|
| Files changed | 3 |
| Lines added | +145 |
| Lines deleted | -12 |
| File types | ts, md |

⚠️ Identified Risks
- No significant risks detected

💡 Improvement Suggestions
- Add unit tests covering the new/changed functionality

---
🤖 Automated review by Claude Code PR Reviewer Agent
```

### PR #2: Bug fix
```
🤖 AI Code Review — django/django#18000

Review Date: 2026-05-22
Confidence Score: High

📋 Summary
This PR modifies 1 file (django/db/models/query.py), adding 8 lines and 
removing 3 lines. The changes appear balanced between additions and modifications.

📊 Diff Stats
| Metric | Value |
|--------|-------|
| Files changed | 1 |
| Lines added | +8 |
| Lines deleted | -3 |
| File types | py |

⚠️ Identified Risks
- No significant risks detected

💡 Improvement Suggestions
- Add type hints to new Python functions for better maintainability

---
🤖 Automated review by Claude Code PR Reviewer Agent
```

# claude-review — PR Review Sub-Agent

Analyzes a GitHub PR diff and produces a structured Markdown review with
identified risks and actionable improvement suggestions.

## Quick Start

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

| Argument   | Required | Description                              |
|-----------|----------|------------------------------------------|
| `--pr`    | Yes      | Full GitHub PR URL                       |
| `--output`| No       | Write review to file (default: stdout)   |

### Examples

```bash
# Output to terminal
./claude-review --pr https://github.com/vercel/next.js/pull/94549

# Save to file
./claude-review --pr https://github.com/vercel/next.js/pull/94549 --output review.md

# GitHub Action (CI-ready)
GITHUB_TOKEN=ghp_xxx ./claude-review --pr https://github.com/org/repo/pull/1
```

## Output Structure

```
## AI Code Review

**Confidence:** 🟢 High / 🟡 Medium / 🔴 Low

### Summary of Changes
- Files changed, lines added/removed, risk/suggestion counts
- File type distribution

### Identified Risks
- ⚠️ Debug print/log statements
- ⚠️ TODO/FIXME still in code
- ⚠️ Hardcoded secrets or tokens

### Improvement Suggestions
- 💡 Add tests
- 💡 Split large PRs
- 💡 Remove dead code / unused imports
```

## Acceptance Criteria

- [x] Works via CLI: `./claude-review --pr <url>`
- [x] Structured Markdown: summary, risks, suggestions, confidence
- [x] Tested on real PRs (vercel/next.js)
- [x] README with setup and usage
- [x] Zero external dependencies (stdlib only)

## Requirements

- Python 3.8+
- No pip install needed

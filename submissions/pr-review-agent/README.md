# Claude Code PR Review Agent

A Claude Code sub-agent that reviews GitHub PRs and generates structured Markdown reports.

## Quick Start

```bash
# Install
curl -sL https://raw.githubusercontent.com/laogongcy-del/claude-builders-bounty/main/submissions/pr-review-agent/claude-review.sh -o /usr/local/bin/claude-review && chmod +x /usr/local/bin/claude-review

# Review a PR
claude-review --pr https://github.com/owner/repo/pull/123
```

Or as a Claude Code skill — place in your project and invoke via `/claude-review`.

## CLI Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
gh pr view 123 --json title,body,additions,deletions,files,changedFiles | claude-review --stdin
```

## Output Structure

The review generates a structured Markdown report with:

```
# 🔍 PR Review: Title

## Summary
2-3 sentence summary of the change scope and size.

## Details
| Field       | Value       |
|-------------|-------------|
| PR #        | 123         |
| State       | open        |
| Files       | 5           |
| Additions   | 120         |
| Deletions   | 30          |

## 🚨 Identified Risks
- ⚠️ Specific risks found in the diff

## 💡 Improvement Suggestions
- Specific suggestions for improvement

## Confidence Score
**High** 🟢 / **Medium** 🟡 / **Low** 🔴
```

## GitHub Action

See `.github/workflows/pr-review.yml` for the GitHub Action integration that
automatically reviews every PR.

## Checks Performed

- Credential/secret leak detection
- Debug code detection (console.log, debugger, etc.)
- TODO/FIXME tracking
- Large file detection
- Missing error handling
- TypeScript `any` type usage

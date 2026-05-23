# claude-review – AI Code Review Sub-Agent

A CLI tool that performs automated code review on GitHub Pull Requests.
Built for the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) program. Issue #4.

## Features

- **CLI-based:** `claude-review --pr https://github.com/owner/repo/pull/123`
- **GitHub Action:** Triggers on PR open/sync and `/review` comments
- **Structured output:** Summary, Risks (with severity), Suggestions, Confidence Score
- **Zero dependencies** beyond Python 3 standard library

## Quick Start

```bash
# Set your GitHub token
export GH_TOKEN=your_github_pat
# or GITHUB_TOKEN
export GITHUB_TOKEN=your_github_pat

# Review a PR
python claude-review --pr https://github.com/owner/repo/pull/123

# JSON output (for programmatic use)
python claude-review --pr https://github.com/owner/repo/pull/123 --json
```

## Requirements

- Python 3.8+
- GitHub token with `repo` scope (for private repos) or `public_repo` scope

## Output Format

The tool generates structured Markdown:

```markdown
# Code Review

**PR:** feat: add new feature
**Author:** @contributor
**Branch:** `feature-branch` -> `main`
**State:** open

## Summary
Introduces **42 additions** and **8 deletions** across **3 file(s)**.

## Risks (2 found)
| Severity | File | Description |
|----------|------|-------------|
| **MEDIUM** | `src/app.ts` | Empty catch block swallowing errors |
| **LOW** | `README.md` | Bare except catches too broadly |

## Suggestions (1 items)
1. PR description is brief - add more context

## Confidence Score
**85/100** - High confidenceorate score
```

## Risk Severity Levels

| Level | Meaning |
|-------|---------|
| **HIGH** | Security issues (hardcoded secrets, PATs, JWTs, private keys, injection) |
| **MEDIUM** | Large changes, empty catch blocks, huge PRs |
| **LOW** | Bare except clauses, wide blast radius (many files touched) |

## Analysis Engine

The tool performs **heuristic scanning** (no AI call needed):

- **Security:** Detects hardcoded credentials, GitHub PATs, JWT tokens, private keys, command injection
- **Code quality:** Flags debug statements (console.log, print(), debugger), TODO/FIXME/HACK markers
- **Structural:** Identifies empty catch blocks, bare except clauses, large file changes
- **Readability:** Checks PR description completeness, file count, total additions

## GitHub Action Usage

Copy `.github/workflows/claude-review.yml` into your repository. The action:

1. Runs on every PR open, sync, or `/review` comment
2. Posts a sticky comment with the review results
3. Uses the built-in `GITHUB_TOKEN` (no PAT needed)

Trigger manual review by commenting `/review` on a PR.

## CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `--pr` | GitHub PR URL (required) | - |
| `--token` | GitHub PAT | `GH_TOKEN` or `GITHUB_TOKEN` env |
| `--json` | Output JSON instead of Markdown | false |
| `--model` | Model name (display only) | `claude-sonnet-4-20250514` |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Review complete, no HIGH-severity issues |
| 1 | HIGH-severity risk(s) found – CI should fail |

## License

MIT

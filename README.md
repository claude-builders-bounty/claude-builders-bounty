# claude-review — PR Review Sub-agent

A CLI tool that analyzes GitHub PR diffs and produces structured Markdown reviews — **summary, risks, suggestions, and confidence score**.

Built as a Claude Code sub-agent. Zero external dependencies, Python 3.7+.

## Quick Start

```bash
# 1. Download
curl -O https://raw.githubusercontent.com/laojinpassion/claude-builders-bounty/bounty-pr-review-agent/claude-review

# 2. Make executable
chmod +x claude-review

# 3. Review any PR
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

```bash
# Review by URL
claude-review --pr https://github.com/torvalds/linux/pull/123

# Review by number + repo
claude-review -p 123 -r owner/repo

# Save output to file
claude-review --pr https://github.com/owner/repo/pull/123 -o review.md

# Quiet mode (no progress messages)
claude-review --pr https://github.com/owner/repo/pull/123 -q
```

For higher API rate limits (private repos, or >60 requests/hour), set your GitHub token:

```bash
export GITHUB_TOKEN=ghp_xxx
```

## Output Structure

Each review contains four sections:

### 📋 Summary
- PR title, author, branches
- Files changed, additions/deletions, file types

### ⚠️ Risks & Concerns
Static analysis detects issues like:
- **🔴 Hardcoded secrets** — passwords, API keys, tokens in code
- **🔴 SQL injection** — string concatenation in SQL queries
- **🟡 Debug code** — print(), console.log, debugger, TODO/FIXME
- **🟡 Large changes** — files >200 lines changed
- **🟡 Dependency updates** — package.json, requirements.txt, etc.
- **🟢 Commented-out code** — dead code that should be removed

### 💡 Suggestions
Actionable recommendations:
- PR scope warnings (>500 lines)
- Missing descriptions
- Missing test coverage
- Binary asset verification

### 📊 Confidence Score
Aggregate quality score (10–100) based on:
- PR size and scope
- Risk severity and count
- Documentation quality
- Test coverage indicators

## Tests

Sample reviews are in `tests/`:
- [`tests/review-1398.md`](tests/review-1398.md) — CHANGELOG generator PR
- [`tests/review-1409.md`](tests/review-1409.md) — Destructive command guard PR

## Requirements

- Python 3.7+
- No pip packages needed (stdlib only)
- Network access to `api.github.com`

## How it works

1. Fetches PR metadata and unified diff via GitHub API
2. Parses the diff into structured file changes and hunks
3. Runs static analysis against curated risk patterns
4. Generates structured Markdown review with color-coded severity

No AI API required — purely static analysis that runs locally and instantly.

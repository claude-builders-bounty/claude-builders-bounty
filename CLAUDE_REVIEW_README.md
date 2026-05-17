# Claude Code PR Review Agent 🤖

> **Bounty #4** — $150 via [Opire](https://opire.dev) — auto-pay on merge

A CLI tool that takes a GitHub PR URL, fetches the diff via the GitHub API,
sends it to Claude for analysis, and returns a structured Markdown review with:

- **Summary** — 2–3 sentence high-level overview
- **Identified Risks** — regressions, breaking changes, performance, race conditions
- **Improvement Suggestions** — actionable code quality & architecture feedback
- **Security Concerns** — injection vectors, secrets exposure, unsafe patterns

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty
```

### 2. Install dependencies
```bash
pip install requests
```

### 3. Set API keys
```bash
# Required — get yours at https://console.anthropic.com/
export ANTHROPIC_API_KEY=sk-ant-...

# Optional — needed for --post-comment and higher GitHub API rate limits
export GITHUB_TOKEN=ghp_...
```

---

## Usage

### Basic review (prints to stdout)
```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

### Save review to a file
```bash
./claude-review --pr https://github.com/owner/repo/pull/123 -o review.md
```

### Post review as a PR comment
```bash
# Requires GITHUB_TOKEN
./claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

### Custom Claude model
```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --model claude-opus-4-20250514
```

---

## GitHub Action (CI)

The file `claude-review-workflow.yml` is a ready-to-use GitHub Action.
Copy it to `.github/workflows/claude-review.yml` in your target repository:

```bash
cp claude-review-workflow.yml /path/to/your-repo/.github/workflows/claude-review.yml
```

Then set the `ANTHROPIC_API_KEY` secret in your repo's Settings → Secrets and variables → Actions.

The action runs automatically on every PR open, push, or reopen.

---

## Example Output

```
# PR Review: myorg/myrepo#42

**PR:** [Fix race condition in payment processing](https://github.com/myorg/myrepo/pull/42)

---

## Summary
This PR fixes a race condition in the payment processing pipeline by adding
a distributed lock around the charge creation step. It also refactors the
retry logic into a shared utility module.

## Identified Risks
- The distributed lock uses Redis with a 30s TTL — if payment processing
  takes longer than 30s, the lock expires and a duplicate charge could
  still occur
- The retry utility changes the default backoff strategy from linear to
  exponential, which may surprise consumers

## Improvement Suggestions
- Consider adding a lock-extension heartbeat loop for long-running payments
- Add integration test for the TTL-expiry edge case
- Document the backoff strategy change in the refactored retry utility's
  docstring

## Security Concerns
- No security concerns identified.
```

---

## Requirements

| Component | Required | Purpose |
|-----------|----------|---------|
| Python 3.8+ | ✅ | Runtime |
| `requests` | ✅ | HTTP client for GitHub & Claude APIs |
| `ANTHROPIC_API_KEY` | ✅ | Claude API authentication |
| `GITHUB_TOKEN` | ⚠️ Optional | PR comment posting + higher rate limits |

---

## Architecture

```
claude-review (CLI)
  ├── parse_pr_url()        → Extract owner/repo/number from URL
  ├── fetch_pr_info()       → GET /repos/{owner}/{repo}/pulls/{number}
  ├── fetch_pr_files()      → GET /repos/{owner}/{repo}/pulls/{number}/files
  ├── build_diff_text()     → Assemble unified diff from file patches
  ├── call_claude()         → POST https://api.anthropic.com/v1/messages
  └── post_pr_comment()     → POST comment back to PR (optional)
```

---

*Part of the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) · Bounty #4 · MIT License*

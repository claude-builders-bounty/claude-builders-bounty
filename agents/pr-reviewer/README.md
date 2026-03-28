# claude-review

A Claude Code sub-agent that reviews a GitHub pull request and produces a structured Markdown review — with optional automatic comment posting.

## Features

- Fetches PR diff and metadata via the `gh` CLI
- Calls Claude (Anthropic SDK or `claude` CLI) for intelligent analysis
- Structured output: **Summary / Risks / Suggestions / Verdict**
- Confidence scoring based on diff size, test coverage, security-sensitive files
- Skips generated files (`package-lock.json`, `*.min.js`, etc.) and binary files
- Truncates very large diffs automatically (configurable)
- Posts review comment directly to the PR (`--post-comment`)
- `--dry-run` mode for CI previews
- Per-repo config via `.claude-review.yml`
- Exit codes for CI gates: `0`=LOW risk, `1`=MEDIUM risk, `2`=HIGH risk

---

## Requirements

| Tool | Purpose |
|------|---------|
| Python 3.9+ | Runtime |
| `gh` CLI | Fetch PR diff & post comments |
| `ANTHROPIC_API_KEY` **or** `claude` CLI | Call Claude |

Install the Anthropic SDK (recommended):

```bash
pip install anthropic
```

Or install `claude` CLI and authenticate:

```bash
npm install -g @anthropic-ai/claude-code
claude auth
```

Authenticate `gh`:

```bash
gh auth login
```

---

## Install

```bash
# Clone (or copy just this agent)
git clone https://github.com/claude-builders-bounty/claude-builders-bounty
cd claude-builders-bounty/agents/pr-reviewer

# Make executable
chmod +x claude_review.py

# Optional: add to PATH
ln -s "$(pwd)/claude_review.py" /usr/local/bin/claude-review
```

---

## Usage

### Basic review (prints to stdout)

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

### Post review as a PR comment

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

### Dry run (print but don't post)

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --post-comment --dry-run
```

### Save output to a file

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

### Custom diff truncation limit

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --max-diff 20000
```

### Use a custom config file

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --config /path/to/.claude-review.yml
```

---

## Config file (`.claude-review.yml`)

Place in your project root (or `~/.claude-review.yml` for global defaults):

```yaml
# .claude-review.yml
max_diff_chars: 30000
skip_patterns:
  - "docs/"
  - "*.generated.ts"
post_comment: false
```

---

## Exit codes

| Code | Meaning | Use in CI |
|------|---------|-----------|
| `0`  | LOW risk | Pass |
| `1`  | MEDIUM risk | Warning / optional gate |
| `2`  | HIGH risk | Fail / block merge |

Example CI usage:

```yaml
- name: PR Review
  run: claude-review --pr ${{ github.event.pull_request.html_url }} --post-comment
  # exits 2 on high risk — CI step fails automatically
```

---

## Review structure

Every review contains:

```
## Summary
2–3 sentences on what the PR does.

## Risks
- Bulleted list of concrete risks

## Suggestions
- Bulleted list of improvement ideas

## Verdict
**Confidence:** High / Medium / Low
**Risk level:** LOW / MEDIUM / HIGH
**Recommendation:** APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION
```

### Confidence scoring

| Factor | Effect |
|--------|--------|
| Diff < 100 lines, ≤ 5 files | Confidence: High |
| Diff < 500 lines, ≤ 20 files | Confidence: Medium |
| Larger | Confidence: Low |
| Security-sensitive files touched | Risk bumped to HIGH |
| No test changes for non-trivial diff | Risk bumped to MEDIUM |

---

## GitHub Action

See [`.github/workflows/pr-review.yml`](../../.github/workflows/pr-review.yml) for a ready-to-use workflow that triggers on every pull request.

---

## Examples

- [Sample review 1](../../examples/sample-review-1.md)
- [Sample review 2](../../examples/sample-review-2.md)

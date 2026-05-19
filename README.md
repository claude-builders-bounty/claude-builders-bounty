# claude-review — PR Review Sub-Agent

A Claude Code sub-agent that analyzes GitHub PR diffs and returns structured Markdown review comments.

## Usage

```bash
# CLI mode
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Requirements

- Python 3.8+
- `GITHUB_TOKEN` environment variable with `repo` scope

## Setup

```bash
export GITHUB_TOKEN=ghp_xxx
```

## Output

The tool generates a structured review with:

| Section | Description |
|---------|-------------|
| **Summary** | Overview of changes (files, additions, deletions) |
| **Changed Files** | List of modified files with diff stats |
| **🔴 Risks** | Security issues, SQL injection, large changes |
| **🟡 Improvements** | Debug output, TODOs, code quality |
| **🟢 Positives** | What's done well |
| **Confidence Score** | Low / Medium / High |

## GitHub Action

Add `.github/workflows/pr-review.yml` to your repo:

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Run claude-review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          curl -sL https://raw.githubusercontent.com/niufox/claude-builders-bounty/main/claude-review.py \
            -o /tmp/claude-review.py
          python3 /tmp/claude-review.py \
            --pr "https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }}" \
            --output review.md
          cat review.md >> $GITHUB_STEP_SUMMARY
```

## Sample Outputs

### Test 1: PR #1678 — generate-changelog skill ($50)

**Confidence: High** — Clean PR, no risks detected.

### Test 2: PR #1682 — Pre-tool-use hook ($100)

**Confidence: Low** — Flagged bare exception handler and debug `print()` in hook script.

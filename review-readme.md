# claude-review — AI-powered PR Review CLI

A CLI tool that analyzes a GitHub PR diff and posts a structured Markdown review comment.

## Features

- **CLI usage**: One command to review any public PR
- **Structured output**: Summary, risks, suggestions, confidence score
- **Risk detection**: Hardcoded secrets, large files, debug prints
- **Test coverage check**: Warns when PR lacks test changes
- **GitHub Action**: Can run automatically on every PR

## Install

```bash
# Requirements: gh CLI (authenticated) and jq
# Just copy the script somewhere in your PATH
cp claude-review /usr/local/bin/
chmod +x /usr/local/bin/claude-review
```

## Usage

```bash
# Full URL
claude-review --pr https://github.com/owner/repo/pull/123

# Shorthand
claude-review --pr owner/repo#123

# Just the PR number (when run from inside a clone of the repo)
cd my-project
claude-review --pr 42
```

## GitHub Action

Add this workflow to `.github/workflows/claude-review.yml` for automatic reviews:

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: sudo apt-get update && sudo apt-get install -y jq
      - name: Review PR
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          chmod +x claude-review
          ./claude-review --pr ${{ github.event.pull_request.number }}
```

Copy `claude-review` into your repo root and add the workflow file — every PR gets an automatic review comment.

## What it checks

| Check | What it looks for |
|-------|-------------------|
| Hardcoded secrets | `password=`, `api_key=`, `token=` in new code |
| Debug prints | `console.log`, `print()`, `fmt.Print` left in |
| TODO/FIXME | Unresolved comments in new code |
| Large files | Files with 200+ line changes |
| Missing tests | PR has source changes but no test files |
| Confidence score | Low/Medium/High based on diff size and test presence |

## Sample Output

### Test 1: PR #1405 — CHANGELOG generator (4 files, +380/-0)

```
## PR Review: Add structured CHANGELOG generator from git history

### Summary
This PR by @rebel117 modifies 4 file(s) across md,sh (+380/-0 lines),
targeting the main branch. No test changes are included.

### Identified risks
- No high-risk patterns detected in the diff

### Improvement suggestions
- No test files found in this PR — consider adding tests

### Confidence: Medium
```

### Test 2: PR #1409 — Destructive command guard (3 files, +584/-0)

```
## PR Review: [BOUNTY $100] Destructive command guard hook

### Summary
This PR by @laojinpassion modifies 3 file(s) across md,py (+584/-0 lines),
targeting the main branch. Test coverage is included.

### Identified risks
- Large change: hooks/pre-tool-use/destructive-command-guard.py — consider splitting
- Large change: test_guard.py — consider splitting

### Improvement suggestions
- 4 debug print statement(s) found — remove before merging

### Confidence: High
```

## Requirements

- `gh` CLI — authenticated with `gh auth login`
- `jq` — for JSON parsing

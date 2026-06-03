# 🤖 claude-review — PR Review Sub-Agent

A Claude Code sub-agent that reviews GitHub PRs and posts structured review comments. Pattern-based static analysis — no API key needed.

## Features

- ✅ Fetches any public PR diff via URL
- ✅ Detects: large PRs, TODOs/FIXMEs, hardcoded secrets, debug code, missing tests
- ✅ Generates structured Markdown: Summary → Risks → Suggestions → Confidence
- ✅ Works locally or as a GitHub Action
- ✅ Zero external dependencies (bash + curl)

## Quick Start (CLI)

```bash
# Review a PR
bash claude-review.sh --pr https://github.com/owner/repo/pull/123

# Save output to file
bash claude-review.sh --pr https://github.com/owner/repo/pull/123 --output review.md

# Review from a local diff file
bash claude-review.sh --diff ./changes.diff
```

## GitHub Action Setup

Add `.github/workflows/pr-review.yml` to your repo:

```yaml
name: PR Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          curl -sL -O https://raw.githubusercontent.com/[...]/claude-review.sh
          bash claude-review.sh --pr "${{ github.event.pull_request.html_url }}"
```

The script auto-detects `GITHUB_TOKEN` from the environment.

## Output Example

```markdown
## 🔍 PR Review

### 📊 Summary
- **Files changed:** 5
- **Additions:** +142  **Deletions:** -38
- **Total changes:** 180 lines

### ⚠️ Identified Risks
- 🔴 3 TODO/FIXME markers found in new code
- 🔴 1 potential hardcoded secret detected

### 💡 Improvement Suggestions
- ✅ Address TODO/FIXME items before merge
- ✅ Use environment variables for credentials

### 🎯 Confidence Score
**Medium**
```

## How It Works

1. Fetches PR diff from GitHub API (or reads local file)
2. Analyzes: file sizes, risk patterns (TODOs, secrets, debug code)
3. Checks: test coverage, dependency changes, commented code
4. Outputs structured Markdown review

## Detection Rules

| Rule | Risk | Description |
|------|------|-------------|
| Large PR | Higher | >500 lines is hard to review |
| TODO/FIXME | Medium | Incomplete work |
| Hardcoded secrets | Critical | API keys, tokens in code |
| Debug statements | Low | console.log, print, debugger |
| No test changes | Suggestion | Code changes without tests |
| Large single file | Medium | >200 line addition in one file |
| Dependency changes | Suggestion | Review for compatibility |

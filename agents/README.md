# Claude Code PR Reviewer Agent

Automated PR reviewer that analyzes diffs and posts structured Markdown comments.

## Features

- ✅ CLI tool: `claude-review --pr <url>`
- ✅ GitHub Action: Automatic review on PR events
- ✅ Structured Markdown output with:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence score (High/Medium/Low)
- ✅ Detects sensitive files, breaking changes, missing tests
- ✅ Posts review comments directly to PR

## Installation

### CLI Tool

```bash
# Make executable
chmod +x agents/claude-review.py

# Optional: Add to PATH
sudo ln -s $(pwd)/agents/claude-review.py /usr/local/bin/claude-review
```

### GitHub Action

Add to `.github/workflows/pr-review.yml`:

```yaml
name: PR Reviewer
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run PR Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python agents/claude-review.py --pr ${{ github.event.pull_request.html_url }} --post
```

## Usage

### CLI

```bash
# Generate review (stdout)
claude-review --pr https://github.com/owner/repo/pull/123

# Post review to PR
claude-review --pr https://github.com/owner/repo/pull/123 --post

# Output as JSON
claude-review --pr https://github.com/owner/repo/pull/123 --json
```

### Output Example

```markdown
## 🔍 PR Review

### 📋 Summary
This PR modifies 5 file(s) with 150 additions and 30 deletions. Primary file types: .py (3), .md (1), .yml (1). Author: username.

### ⚠️ Identified Risks
- Large PR (>500 lines changed) - consider splitting into smaller PRs for easier review
- Potential credentials in code - verify these are not hardcoded secrets

### 💡 Improvement Suggestions
- No test files modified - consider adding tests for new functionality
- Significant code changes without documentation updates

### 📊 Confidence Score
🟡 **Medium**

### 📈 Statistics
- **Additions:** 150
- **Deletions:** 30
- **Changed Files:** 5
```

## Detection Patterns

### Risks
- Large PRs (>500 lines)
- Sensitive files (.env, keys, credentials)
- Breaking changes (BREAKING, remove, deprecate)
- Private key files

### Suggestions
- Missing tests
- Missing documentation
- TODO/FIXME comments

## Requirements

- Python 3.7+
- GitHub CLI (`gh`) authenticated
- `GITHUB_TOKEN` for GitHub Action

## License

MIT

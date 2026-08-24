# Claude Code PR Reviewer Agent

## Overview
A CLI tool + GitHub Action that reviews GitHub PRs using Claude Code and posts structured Markdown reviews.

## Installation
```bash
curl -fsSL https://raw.githubusercontent.com/kramsg1405/vega-bounties/main/claude-pr-reviewer/claude_reviewer.py -o claude_reviewer.py
chmod +x claude_reviewer.py
```

## Usage

### CLI
```bash
export GITHUB_TOKEN=ghp_xxxxx  # GitHub PAT with repo scope
python3 claude_reviewer.py --pr https://github.com/owner/repo/pull/123
```

### GitHub Action
Copy `.github/workflows/pr-review.yml` to your repo's `.github/workflows/` directory.

The workflow triggers on PR open/synchronize and posts a review comment.

## Output Format
```markdown
## 🤖 Automated PR Review

### Summary
2-3 sentence summary of changes

### ⚠️ Identified Risks
- Risk 1
- Risk 2

### 💡 Improvement Suggestions
- Suggestion 1
- Suggestion 2

### 🎯 Confidence Score
**Medium**
```

## Requirements
- Python 3.8+
- `GITHUB_TOKEN` environment variable
- Optional: `claude` CLI installed for live AI reviews (falls back to structured stub)

## Testing
```bash
# Test on a real PR
python3 claude_reviewer.py --pr https://github.com/kramsg1405/test-repo/pull/1
```
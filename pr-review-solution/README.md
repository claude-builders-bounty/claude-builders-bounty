# PR Review Agent

Automated GitHub PR review tool that analyzes diffs and posts structured feedback.

## Features

- **CLI tool** — review any PR from the command line
- **GitHub Action** — auto-review PRs on open/sync
- **Structured output** — Summary, Risks, Suggestions, Confidence score
- **Security scanning** — detects hardcoded secrets, injection risks
- **Code quality** — flags TODOs, debug statements, type issues

## Usage

### CLI

```bash
# Review a PR (output to terminal)
python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# Review and post comment
python3 claude-review.py --pr owner/repo#123 --post

# Save to file
python3 claude-review.py --repo owner/repo --number 123 -o review.md
```

### GitHub Action

Copy `.github/workflows/pr-review.yml` to your repo. It will auto-review every PR on open/sync.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GH_TOKEN` | Yes | GitHub Personal Access Token |
| `ANTHROPIC_API_KEY` | No | For enhanced analysis (uses pattern matching if not set) |

## Output Format

```markdown
## 🔍 Automated PR Review

### 📝 Summary
This PR modifies **3 file(s)** with **45 additions** and **12 deletions**.

### ⚠️ Risks
- 🔒 Hardcoded API key detected
- ⚠️ Large change in src/app.ts (300 lines)

### 💡 Suggestions
- 💡 Consider removing console.log() before production
- 💡 TODO comment found — ensure it's tracked

### 📊 Confidence: **Medium**
```

## Setup

1. Set `GH_TOKEN` environment variable
2. Run: `pip install requests`
3. Run: `python3 claude-review.py --pr <url>`

## Requirements

- Python 3.8+
- `requests` package
- GitHub token with `repo` scope

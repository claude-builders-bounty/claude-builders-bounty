# Claude Code PR Review Agent 🤖

A lightweight CLI tool (and GitHub Action) that fetches a GitHub PR diff and uses **Claude** (Anthropic) to produce a structured, actionable code review in Markdown.

## Features

- ✅ Zero runtime dependencies — pure Python 3 stdlib
- ✅ Works with public repos (no token needed) and private repos (`GH_TOKEN`)
- ✅ Structured Markdown output: Summary, Risks, Suggestions, Confidence Score
- ✅ GitHub Actions workflow included — posts review as a PR comment automatically
- ✅ Configurable model (defaults to `claude-sonnet-4-5`)

---

## Requirements

| Requirement | Notes |
|---|---|
| Python 3.8+ | No third-party packages needed |
| `ANTHROPIC_API_KEY` | **Required** — get one at [console.anthropic.com](https://console.anthropic.com) |
| `GH_TOKEN` (optional) | Required for private repos; increases rate limits for public repos |

---

## Quick Start

### 1. Clone / download

```bash
git clone https://github.com/your-org/claude-pr-review.git
cd claude-pr-review
chmod +x claude-review.sh
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# optional — for private repos or higher GitHub rate limits:
export GH_TOKEN="ghp_..."
```

### 3. Review a PR

```bash
# Using the wrapper script (recommended)
./claude-review.sh --pr https://github.com/django/django/pull/18000

# Or call Python directly
python3 claude-review.py --pr https://github.com/django/django/pull/18000
```

---

## CLI Usage

```
usage: claude-review.py [-h] --pr PR [--model MODEL] [--output OUTPUT] [--json]

options:
  -h, --help       Show this help message and exit
  --pr PR          Full GitHub PR URL (required)
  --model MODEL    Claude model to use (default: claude-sonnet-4-5)
  --output OUTPUT  Write review to a file instead of stdout
  --json           Emit raw JSON response from Anthropic API
```

### Examples

```bash
# Review any public PR (no token needed)
./claude-review.sh --pr https://github.com/facebook/react/pull/31000

# Save review to a file
./claude-review.sh --pr https://github.com/owner/repo/pull/42 --output review.md

# Use a different model
./claude-review.sh --pr https://github.com/owner/repo/pull/42 --model claude-opus-4-5

# Private repo (needs GH_TOKEN)
GH_TOKEN=ghp_xxx ./claude-review.sh --pr https://github.com/my-org/private-repo/pull/7
```

### Output Format

```markdown
## PR Review: owner/repo#123

### Summary
[2-3 sentences describing the change]

### Identified Risks
- [specific risk with file/line references]
- [another risk]

### Improvement Suggestions
- [actionable suggestion]
- [another suggestion]

### Confidence Score: High
```

---

## GitHub Actions Setup

The included workflow (`.github/workflows/claude-review.yml`) runs automatically on every PR and posts the review as a comment.

### Setup Steps

1. **Add your Anthropic API key** to your repo's secrets:
   - Go to **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `ANTHROPIC_API_KEY`
   - Value: `sk-ant-...`

2. **Copy the workflow file** to your repo:
   ```bash
   cp .github/workflows/claude-review.yml YOUR_REPO/.github/workflows/
   ```

3. **Commit and push** — the action will trigger on the next PR.

### Manual Trigger

You can also trigger a review for any PR from the Actions tab:
- Go to **Actions → Claude PR Review → Run workflow**
- Enter the full PR URL

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Yes | Your Anthropic API key |
| `GH_TOKEN` / `GITHUB_TOKEN` | ⚠️ For private repos | GitHub Personal Access Token or Actions token |

---

## Supported Models

Any Claude model accessible via your Anthropic account:

| Model | Notes |
|---|---|
| `claude-sonnet-4-5` | Default — best balance of speed and quality |
| `claude-opus-4-5` | Highest quality, slower |
| `claude-haiku-3-5` | Fastest, cheapest |
| `claude-3-5-sonnet-20241022` | Older sonnet if needed |

---

## Cost Estimate

| PR Size | Approximate Cost |
|---|---|
| Small (< 200 lines) | ~$0.002 |
| Medium (200–1000 lines) | ~$0.008 |
| Large (1000+ lines) | ~$0.02 |

*(Based on `claude-sonnet-4-5` pricing; actual cost depends on diff size.)*

---

## Troubleshooting

**`ANTHROPIC_API_KEY is not set`**
→ Run `export ANTHROPIC_API_KEY=sk-ant-...` before calling the script.

**`GitHub API error 403`**
→ You're likely hitting the unauthenticated rate limit. Set `GH_TOKEN`.

**`GitHub API error 404`**
→ The PR URL may be wrong, or the repo is private and you need `GH_TOKEN`.

**Large diffs truncated**
→ Diffs > 80,000 characters are automatically truncated. The Confidence Score will reflect this (`Medium` or `Low`).

---

## License

MIT — use freely, contributions welcome.

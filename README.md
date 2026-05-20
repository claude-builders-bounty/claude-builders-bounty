# Claude PR Review Agent

AI-powered automated code review that analyzes GitHub PR diffs and produces structured Markdown feedback — summary, risks, suggestions, and confidence score.

## How it works

1. Takes a GitHub PR URL as input
2. Fetches the PR diff via GitHub API
3. Sends the diff to Claude (claude-sonnet-4-20250514) with a structured review prompt
4. Outputs a Markdown code review you can post directly as a PR comment

## Setup

### 1. Install
```bash
chmod +x claude-review
# Optional: add to PATH
cp claude-review /usr/local/bin/
```

### 2. Get API keys
- **Anthropic API key**: https://console.anthropic.com/
- **GitHub token** (optional, for private repos): https://github.com/settings/tokens

### 3. Set environment
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."  # optional
```

### 4. Run
```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

### 5. (Optional) GitHub Action
See `.github/workflows/claude-review.yml` included for CI integration.

## Usage

```bash
# Basic usage
claude-review --pr https://github.com/expressjs/express/pull/6000

# With explicit API key
claude-review --pr https://github.com/owner/repo/pull/1 --api-key sk-ant-xxx

# Save to file
claude-review --pr https://github.com/owner/repo/pull/1 > review.md
```

## Example Output

See [EXAMPLE-OUTPUT.md](EXAMPLE-OUTPUT.md) for a sample review generated from a real PR.

## Requirements

- Python 3.8+
- Anthropic API key (Claude access)
- Internet access (for GitHub + Anthropic APIs)

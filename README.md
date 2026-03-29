# claude-review — CLI PR Reviewer

Bounty #210 - $150

AI-powered pull request reviewer using Claude API. Automatically analyzes PRs and posts structured, helpful reviews.

## Features

- ✅ **Automated PR review** - Fetches PR diff, generates review with Claude
- ✅ **Structured output** - Summary, strengths, concerns, suggestions, verdict
- ✅ **GitHub integration** - Can post review directly as PR comment
- ✅ **Flexible input** - Accepts PR URL or repo+number
- ✅ **Environment variables** - Configure via env vars or CLI args

## Installation

```bash
pip install requests
chmod +x claude_review.py
```

## Usage

### Basic Review (print to stdout)
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."

./claude_review.py --pr-url "https://github.com/owner/repo/pull/123"
```

### Post Review as Comment
```bash
./claude_review.py --pr-url "https://github.com/owner/repo/pull/123" --post
```

### Using Repo + PR Number
```bash
./claude_review.py --repo "owner/repo" --pr-number 123 --post
```

### Save to File
```bash
./claude_review.py --pr-url "https://github.com/owner/repo/pull/123" --output review.md
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key (required) |
| `GITHUB_TOKEN` | GitHub Personal Access Token (required for --post) |

## CLI Options

| Option | Description |
|--------|-------------|
| `--pr-url` | Full PR URL (e.g., `https://github.com/owner/repo/pull/123`) |
| `--repo` | Repository in `owner/repo` format |
| `--pr-number` | PR number |
| `--anthropic-key` | Anthropic API key (or use env var) |
| `--github-token` | GitHub token (or use env var) |
| `--post` | Post review as PR comment |
| `--output` | Save review to file |

## Example Output

```
============================================================
## 🤖 Automated PR Review

### Summary
This PR adds user authentication with JWT tokens and session management.

### Strengths
- Clean separation of concerns
- Good test coverage
- Proper error handling

### Concerns
1. JWT secret should be loaded from environment, not hardcoded
2. Consider adding rate limiting to login endpoint
3. Session timeout could be configurable

### Suggestions
- Move JWT_SECRET to .env file
- Add express-rate-limit middleware
- Add SESSION_TIMEOUT config option

### Verdict: REQUEST_CHANGES
============================================================
```

## License

MIT - Created for claude-builders-bounty #210

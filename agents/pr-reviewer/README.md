# Claude PR Review Agent

> A Claude Code sub-agent that reviews GitHub PRs and generates structured
> Markdown reviews — with static analysis and optional AI-powered review
> via Claude Code CLI.

## How it works

1. **Fetch**: Downloads the PR diff via GitHub API
2. **Analyze**: Runs 10+ security and code-quality pattern checks
3. **Report**: Generates a structured Markdown review with:
   - Summary of changes
   - Identified risks (severity-tagged)
   - Improvement suggestions
   - File-by-file breakdown
   - Overall confidence score

Optionally integrates with **Claude Code CLI** for AI-powered review:
`claude-review --pr <URL> --claude`

## Usage

### CLI (standalone)
```
python scripts/review.py --pr https://github.com/owner/repo/pull/123
GITHUB_TOKEN=ghp_xxx python scripts/review.py --pr https://github.com/owner/repo/pull/123
bash scripts/claude-review.sh --pr https://github.com/owner/repo/pull/123
bash scripts/claude-review.sh --pr https://github.com/owner/repo/pull/123 --claude
```

### GitHub Action (automated)
Copy `.github/workflows/pr-review.yml` into your repo. It auto-reviews every
new PR and posts a structured comment.

## Requirements
- Python 3.6+
- GitHub token (optional, for higher API rate limits)

## Files
| File | Purpose |
|------|---------|
| scripts/review.py | Core analysis engine (Python) |
| scripts/claude-review.sh | CLI wrapper script |
| .github/workflows/pr-review.yml | GitHub Action workflow |

## Security patterns checked
| Pattern | Severity |
|---------|----------|
| Hardcoded credentials | High |
| eval() / exec() | High |
| innerHTML / dangerouslySetInnerHTML | High |
| SQL injection patterns | High |
| Debug statements (console.log, dd) | Medium |
| TODO / FIXME comments | Medium |
| Bare except clauses | Suggestion |
| Type comparison vs identity | Suggestion |

# Claude Code PR Reviewer

An AI-powered GitHub Pull Request reviewer that uses Claude Code to analyze diffs and produce structured, actionable code reviews.

Created for: Nous Research Bounty Program ($150)

---

## Features

- **CLI-first**: Run `claude-review --pr URL` from your terminal
- **GitHub Action**: Automated review on every PR (or triggered by `/claude-review` comment)
- **Structured output**: Summary, identified risks, improvement suggestions, and confidence score
- **Flexible auth**: Uses `gh` CLI when available, falls back to `curl` + `GITHUB_TOKEN`
- **Graceful degradation**: Runs a simulated review when Claude Code is not installed

## Requirements

| Tool | Purpose | Install |
|------|---------|---------|
| **Claude Code** | AI analysis engine | `npm install -g @anthropic-ai/claude-code` |
| **gh** (GitHub CLI) | PR diff fetching (primary) | `brew install gh` / `apt install gh` |
| **curl** | Fallback HTTP client | Pre-installed on most systems |
| **jq** | JSON parsing | `brew install jq` / `apt install jq` |

### API Keys

- **ANTHROPIC_API_KEY**: Required by Claude Code. Set in your environment or `~/.claude.json`.
- **GITHUB_TOKEN**: Only needed if `gh` is not available. Generate at https://github.com/settings/tokens (needs `repo` scope for private repos, `public_repo` for public).

## Quick Start

```bash
# 1. Install Claude Code
npm install -g @anthropic-ai/claude-code

# 2. Authenticate with GitHub (if using gh)
gh auth login

# 3. Run a review
./claude-review.sh --pr https://github.com/nushell/nushell/pull/14567

# 4. Or use short format
./claude-review.sh --pr nushell/nushell#14567
```

## Usage

```
claude-review --pr URL [OPTIONS]

OPTIONS:
    --pr URL         GitHub PR to review (required)
    --timeout SEC    Timeout in seconds (default: 120)
    --model MODEL    Claude model (default: claude-sonnet-4-20250514)
    --help, -h       Show help

ENVIRONMENT:
    GITHUB_TOKEN     GitHub token for curl-based API access
    CLAUDE_BIN       Path to claude CLI (default: claude)
    CLAUDE_MODEL     Claude model to use
```

### URL Formats

- Full URL: `https://github.com/owner/repo/pull/123`
- Short form: `owner/repo#123`

## Output Format

Every review produces a structured Markdown document:

```markdown
============================================
  CLAUDE CODE PR REVIEW
  owner/repo#123
  2026-05-28 16:00:00
============================================

## Summary
[2-3 sentence overview of the PR and assessment]

## Identified Risks
- [Risk with severity]
- [Another risk]
...

## Improvement Suggestions
- [Actionable suggestion]
- [Another suggestion]
...

## Confidence Score
[Low/Medium/High] — [rationale]
```

See [sample-outputs/](sample-outputs/) for real examples.

## GitHub Action Setup

Copy `.github/workflows/claude-review.yml` to your repository's `.github/workflows/` directory.

### Required Secrets

Add these to your repository's Settings → Secrets and variables → Actions:

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `GITHUB_TOKEN` | Automatically provided by GitHub Actions |

### Triggers

The action runs on:
- PR opened, synchronized, reopened, or marked ready for review
- PR review comments
- Issue comments containing `/claude-review`

### Manual Trigger in PR Comments

Comment `/claude-review` on any PR to trigger a review.

## Testing

```bash
# Test with a public PR (no auth needed if gh is authenticated)
./claude-review.sh --pr https://github.com/kubernetes/kubernetes/pull/123456

# Test with timeout override for large PRs
./claude-review.sh --pr owner/repo#42 --timeout 300

# Test with different model
./claude-review.sh --pr owner/repo#42 --model claude-opus-4-20250514
```

## Architecture

```
claude-review.sh
├── Parse --pr URL → owner/repo#number
├── Check dependencies (gh, curl, claude)
├── Fetch PR metadata (title, stats, author)  ← gh pr view / GitHub API
├── Fetch PR diff                              ← gh pr diff / GitHub API
├── Build structured analysis prompt
├── Run Claude Code analysis                   ← claude -p / claude-code --print
└── Format and output structured review
```

## Files

```
/tmp/bounty-4/
├── claude-review.sh              # Main review script
├── README.md                     # This file
├── .github/workflows/
│   └── claude-review.yml         # GitHub Actions workflow
└── sample-outputs/
    ├── example-review-1.md       # Python argparse fix review
    └── example-review-2.md       # React hook optimization review
```

## License

MIT

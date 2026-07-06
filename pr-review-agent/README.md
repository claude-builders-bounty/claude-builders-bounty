# 🔍 Claude Code PR Review Agent

An AI-powered PR review tool that analyzes GitHub pull requests and produces structured Markdown reviews.

## Features

- **CLI mode**: `./claude-review.sh --pr https://github.com/owner/repo/pull/123`
- **GitHub Action**: Auto-reviews every PR and posts a structured comment
- **Static analysis**: Detects risks (hardcoded secrets, debug logging, missing tests)
- **Confidence scoring**: Rates review confidence based on change size and analysis depth

## Quick Start (CLI)

```bash
# Review any public PR
chmod +x claude-review.sh
./claude-review.sh --pr https://github.com/owner/repo/pull/123

# Save to file
./claude-review.sh --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Quick Start (GitHub Action)

1. Copy `.github/workflows/pr-review.yml` to your repo
2. Push — every new PR gets an automated review comment

## Output Structure

Each review includes:
- **PR Overview**: Author, size, files changed
- **Summary of Changes**: Narrative of what the PR does
- **Files Changed**: List of all modified files
- **Identified Risks**: Severity-rated concerns
- **Improvement Suggestions**: Actionable recommendations
- **Best Practices Check**: Code quality metrics
- **Confidence Score**: How reliable the review is

## Test Outputs

See [test-outputs/](./test-outputs/) for example reviews generated on real GitHub PRs.

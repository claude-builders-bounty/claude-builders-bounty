Claude Code PR Review Agent

*A standalone CLI tool that reviews GitHub PRs — **zero API keys required**.*

## ⚡ Quick Start
```bash
bash pr-review.sh --pr https://github.com/owner/repo/pull/123
```

## Output
- Summary of changes
- Identified risks (security, size, debug code)
- Improvement suggestions  
- Confidence score

## Why No API Keys?
The tool uses static heuristic analysis (diff size, file count, keyword scanning).
It works on *any* public GitHub repository instantly.

## GitHub Action (Optional)
Copy `.github/workflows/pr-review.yml` to your repo for automatic PR reviews.
Still zero API keys — uses GitHub's built-in token via `github.token`.

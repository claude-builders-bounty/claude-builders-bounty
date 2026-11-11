# Claude Code Sub-Agent: PR Reviewer

Automated Pull Request Reviewer sub-agent for Claude Code that fetches PR diffs, conducts static and heuristic vulnerability assessments, and generates structured Markdown reviews.

## CLI Usage

```bash
# Set your GitHub Token (optional for public PRs, recommended for rate limits)
export GITHUB_TOKEN="ghp_xxx"

# Run review via CLI
python3 agents/claude-review/claude_review.py --pr https://github.com/owner/repo/pull/123
```

## GitHub Action Workflow
Include `.github/workflows/claude-review.yml` in your repository. It automatically reviews every opened or synchronized pull request and posts the structured review directly to the PR comment thread.

## Sample Review Outputs
Sample outputs tested against real pull requests are available in `agents/claude-review/sample_reviews/`.

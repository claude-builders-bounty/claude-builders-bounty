# PR Review Agent

Claude Code sub-agent that analyzes PR diffs and returns structured Markdown reviews.

## CLI Usage

```bash
export GITHUB_TOKEN="ghp_..."
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
```

With Claude API (for AI-powered analysis):
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
```

## GitHub Action

Add `.github/workflows/pr-review.yml` to auto-review every PR.

## Output

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score (Low/Medium/High)

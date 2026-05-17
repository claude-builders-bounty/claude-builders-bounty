# SKILL.md — PR Review Agent

## Description
Automatically reviews a GitHub PR and posts a structured Markdown comment.  
Works via CLI (`python pr_review.py --pr <url>`) or GitHub Action (auto-reviews on PR open).

## Usage

### Option A: CLI
```bash
# Set environment variables
export GITHUB_TOKEN="ghp_xxx"
export CLAUDE_API_KEY="sk-ant-xxx"

# Run review
python pr_review.py --pr https://github.com/owner/repo/pull/123

# Optionally post as comment
python pr_review.py --pr https://github.com/owner/repo/pull/123 --post-comment
```

### Option B: GitHub Action (Automatic)
Add to your repo:
```yaml
# .github/workflows/pr-review.yml
name: PR Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run PR Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
        run: |
          pip install urllib3
          python pr_review.py --pr ${{ github.event.pull_request.html_url }} --post-comment
```

### Option C: Claude Code Command
In Claude Code:
```
/review-pr https://github.com/owner/repo/pull/123
```

## Output Format

```markdown
## Summary
This PR adds a new pre-commit hook that blocks destructive bash commands...

## Identified Risks
- **High**: The hook doesn't handle edge cases where `rm -rf` is in a script
- **Medium**: No tests for Windows compatibility
- **Low**: Documentation could be clearer

## Improvement Suggestions
- Add unit tests for each blocked command pattern
- Handle edge case: `rm -rf` inside shell scripts
- Add configuration file for custom rules
- Include examples in README

## Confidence Score: **High**
(review is based on clear code changes and established best practices)
```

## Requirements
- Python 3.8+
- GitHub Token (for API access)
- Claude API Key (for analysis)

## Notes
- Uses `claude-sonnet-4-20250514` model as required
- Auto-posts comment if `--post-comment` flag is set
- Saves review to `review_output.md` for inspection

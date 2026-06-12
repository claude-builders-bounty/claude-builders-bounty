# Claude PR Review Agent

Claude Code sub-agent that reviews GitHub PRs.

## CLI Usage

```bash
python review_pr.py --pr https://github.com/owner/repo/pull/123
```

Outputs structured Markdown with summary, risks, suggestions, and confidence score.

## GitHub Action

Add to your repo:

```yaml
# .github/workflows/pr-review.yml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: |
          python review_pr.py \
            --pr "\${{ github.event.pull_request.html_url }}" \
            --github-token "\${{ secrets.GITHUB_TOKEN }}"
```

## Sample Output

```
## PR Review: https://github.com/owner/repo/pull/123

### Summary
Changes 3 file(s) (+45/-12 lines). Adds user profile API endpoint.

### Identified Risks
- ⚠️ Debug console.log statements detected.

### Improvement Suggestions
- 💡 No tests detected. Consider adding tests.

**Confidence Score**: Medium
```

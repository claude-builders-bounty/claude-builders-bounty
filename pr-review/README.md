# PR Review Agent (Bounty #4)

A **Claude Code sub-agent** that reviews GitHub PRs and posts structured Markdown comments.

## CLI Usage

```bash
# With GITHUB_TOKEN environment variable
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
python claude-review.py --pr https://github.com/owner/repo/pull/123

# Preview mode (generate sample outputs without real PRs)
python claude-review.py --preview

# Custom output path
python claude-review.py --pr https://github.com/owner/repo/pull/123 --output my-review.md
```

## GitHub Action Usage

Add this workflow to your repo as `.github/workflows/pr-review.yml`:

```yaml
name: PR Review
on:
  pull_request_target:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run PR Review
        run: |
          python claude-review.py \
            --pr https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }} \
            --output review-output.md
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Post Comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const body = fs.readFileSync('review-output.md', 'utf-8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

## Output Format

Each review includes:
- **Summary** of changes (2-3 sentences)
- **Identified risks** with severity levels
- **Improvement suggestions**
- **Confidence score**: Low / Medium / High

## What It Checks

### Security Risks
- Hardcoded credentials (passwords, API keys, tokens)
- SQL injection patterns
- use of eval/exec
- Insecure HTTP URLs

### Code Quality
- Debug prints left in code
- Unresolved TODO/FIXME
- Bare except blocks
- Missing type annotations
- Missing docstrings

### Style & Maintainability
- Lines exceeding 100 chars
- Magic numbers
- Wildcard imports
- Large files that should be split

## Requirements

- Python 3.8+
- `GITHUB_TOKEN` environment variable (GitHub Personal Access Token)

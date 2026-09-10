# PR Reviewer Agent

CLI + GitHub Action that posts a **structured Markdown review** of a pull request.

## CLI (2 commands)

```bash
export GITHUB_TOKEN=ghp_...   # optional, raises rate limit
python3 agents/pr_reviewer/pr_reviewer.py --pr https://github.com/owner/repo/pull/123
```

Or:

```bash
python3 agents/pr_reviewer/pr_reviewer.py --repo owner/repo --number 123
```

## Output

- Summary of changes (from PR body)
- File list with +/- counts
- Identified risks (CI, auth, migrations, large deletions, draft)
- Improvement suggestions
- Confidence: Low / Medium / High

## GitHub Action

```yaml
# .github/workflows/pr-review.yml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize, reopened]
permissions:
  contents: read
  pull-requests: write
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Generate review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 agents/pr_reviewer/pr_reviewer.py \
            --repo "$GITHUB_REPOSITORY" \
            --number "${{ github.event.pull_request.number }}" \
            | tee review.md
      - name: Comment on PR
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh pr comment "${{ github.event.pull_request.number }}" \
            --repo "$GITHUB_REPOSITORY" \
            --body-file review.md
```

Stdlib only — no pip install required.

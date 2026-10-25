# Claude Code PR Reviewer Sub-Agent

> 🤖 An autonomous code reviewer that inspects Pull Request diffs and posts structured Markdown reviews.
> Solves **[Bounty #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)** ($150).

---

## ⚡ CLI Usage

```bash
# Review a PR and print structured Markdown
python agents/pr-reviewer/pr_reviewer.py --pr https://github.com/owner/repo/pull/123

# Review and automatically post a comment to GitHub
python agents/pr-reviewer/pr_reviewer.py --pr https://github.com/owner/repo/pull/123 --post-comment
```

---

## ⚙️ GitHub Action Workflow

Place `.github/workflows/pr-reviewer.yml` in your repository:

```yaml
name: Claude Code PR Reviewer

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
          python-version: "3.11"
      - name: Run Reviewer
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python agents/pr-reviewer/pr_reviewer.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --token "$GITHUB_TOKEN" \
            --post-comment
```

---

## 📊 Sample Outputs

Live reviews generated on real GitHub Pull Requests are available in [`samples/`](./samples/):
- [`sample_omi_22218.md`](./samples/sample_omi_22218.md) (BasedHardware/omi #22218)
- [`sample_gohybrid_587.md`](./samples/sample_gohybrid_587.md) (limitlessprojects/Go-Hybrid #587)

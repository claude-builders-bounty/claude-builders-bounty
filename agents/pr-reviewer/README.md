# Claude Code PR Review Sub-Agent

> Autonomous pull request review sub-agent and GitHub Action for automated static analysis, security risk detection, and structured review generation.

---

## ⚡ Quick Setup & Usage

### 1. CLI Usage
Run the sub-agent against any public GitHub Pull Request:

```bash
# Using python directly:
python agents/pr-reviewer/review.py --pr https://github.com/owner/repo/pull/123

# Or with CLI executable:
chmod +x agents/pr-reviewer/claude-review
./agents/pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123

# Save to file or post directly to GitHub:
python agents/pr-reviewer/review.py --pr <URL> --output review.md --token $GITHUB_TOKEN --post
```

### 2. GitHub Action CI Workflow
Include `.github/workflows/claude-pr-review.yml` in your repository. The action triggers automatically on any new or updated pull request:

```yaml
name: Claude Code PR Reviewer
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
          python-version: '3.11'
      - name: Run Review Agent
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python agents/pr-reviewer/review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --token "$GITHUB_TOKEN" \
            --post
```

---

## 📋 Review Structure Output

Each review provides:
1. **Summary of Changes**: 2-3 sentence overview of PR scope and delta.
2. **Identified Risks**: Security scans for destructive commands (`rm -rf`), plain secrets, unvalidated `eval()` execution, and SQL injection risks.
3. **Improvement Suggestions**: Actionable recommendations for test coverage, exception safety, and documentation.
4. **Confidence Score**: Low / Medium / High confidence rating based on diff complexity and risk footprint.

---

## 🧪 Real-World Sample Reviews
- Sample 1 (Review of PR #4227): [`samples/reviews/review_sample_1.md`](../../samples/reviews/review_sample_1.md)
- Sample 2 (Review of PR #4240): [`samples/reviews/review_sample_2.md`](../../samples/reviews/review_sample_2.md)

# Claude Code PR Reviewer Agent 🤖

An automated Pull Request reviewer agent for Claude Code and GitHub Actions that analyzes PR diffs, conducts static and semantic risk evaluation, and generates structured Markdown reviews with confidence scoring.

---

## Output Format

The agent outputs a structured Markdown review:

```markdown
### Summary of Changes
[Concise 2-3 sentence overview of what the PR accomplishes]

### Identified Risks
- [Security, regression, performance, or edge-case risks]

### Improvement Suggestions
- [Actionable recommendations or refactoring improvements]

### Confidence Score
**Confidence**: [High | Medium | Low] — [Reasoning]
```

---

## Usage

### 1. CLI Usage
```bash
# Review a remote PR
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123

# Post comment directly to GitHub
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123 --post-comment --github-token <GH_TOKEN>

# Review local diff file or piped diff
git diff main | python agents/pr-reviewer/claude_review.py
```

### 2. GitHub Actions Setup
Add `.github/workflows/claude-pr-review.yml` to your repository:
```yaml
name: Claude PR Reviewer
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
      - name: Run Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python agents/pr-reviewer/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --post-comment
```

---

## Sample Outputs
- [Sample Review 1 (MergeFi/frontend #507)](examples/sample_review_1.md)
- [Sample Review 2 (Grainlify/Grainlify-Frontend #1073)](examples/sample_review_2.md)

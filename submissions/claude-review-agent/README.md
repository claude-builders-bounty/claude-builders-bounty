# Claude Review Agent

An AI-powered PR review agent that analyzes GitHub PR diffs and generates structured review comments.

## Features

- 🔍 Fetches PR diffs directly from GitHub
- 🤖 Uses Claude CLI for AI-powered analysis (with smart fallback)
- 📊 Structured Markdown output: Summary, Risks, Suggestions, Confidence
- 🚀 Works as CLI tool or GitHub Action

## Installation

```bash
pip install -r requirements.txt
chmod +x claude_review.py
```

## Usage

### CLI Mode
```bash
# Review a GitHub PR
python claude_review.py --pr https://github.com/owner/repo/pull/123

# Review a local diff file
python claude_review.py --diff /path/to/diff.txt
```

### GitHub Action (`.github/workflows/pr-review.yml`)
```yaml
name: AI PR Review
on: [pull_request_target]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - name: Run AI Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python claude_review.py --pr "https://github.com/${{ github.repository }}/pull/${{ github.event.number }}" > review.md
          cat review.md
      - name: Post Review Comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: review
            });
```

## Sample Output

```
## 🔍 PR Review Report

### Summary
This PR modifies 2 file(s): src/api.py, tests/test_api.py
Total changes: +45 lines added, -12 lines removed

### Identified Risks
- ✅ No obvious risks detected

### Improvement Suggestions
- Consider adding error handling for edge cases in the new function

### Confidence Score
**High**
```

## Requirements

- Python 3.8+
- `requests` (optional, for PR fetching)

## License

MIT

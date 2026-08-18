# Claude PR Reviewer Agent

A lightweight, automated sub-agent for **Claude Code** that analyzes Pull Request diffs for security risks, command injection threats, code quality improvements, and provides structured Markdown code reviews with confidence scores.

## 🚀 Quickstart & Usage

### 1. CLI Usage
```bash
# Review a public GitHub Pull Request
python src/claude_review.py --pr https://github.com/expressjs/express/pull/5000

# Review a local patch / diff file
python src/claude_review.py --diff path/to/feature.patch --output review_report.md
```

### 2. GitHub Action Integration
Add to your repository `.github/workflows/pr_review.yml`:
```yaml
name: Automated Claude PR Reviewer
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: ./src/action.yml
```

---

## 🧪 Testing

Run the unit test suite:
```bash
python tests/test_claude_review.py
```
Outputs: `4/4 PASSED`

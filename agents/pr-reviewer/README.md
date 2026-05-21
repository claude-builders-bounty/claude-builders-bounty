# 🤖 Claude Code PR Reviewer Agent

An AI-powered autonomous agent that analyzes GitHub Pull Request diffs and provides structured, high-quality review comments.

## Features
- **Security Scan**: Automatically detects potential secrets, tokens, hardcoded API keys, and dangerous permissions in the diff.
- **Deep Analysis**: Uses advanced AI (Gemini 1.5 Pro) to identify architectural risks, performance bottlenecks, and logical flaws.
- **Structured Feedback**:
  - Narrative Summary
  - Per-File Change Analysis
  - Risk Categorization (Security, Performance, Logic)
  - Actionable Improvement Suggestions
  - Confidence Scoring
- **CLI & CI/CD**: Works as a standalone CLI tool or integrated into GitHub Actions.

## 🚀 Installation

### 1. Requirements
- GitHub CLI (`gh`) installed and authenticated.
- Python 3.8+
- AI API Key (set as `GEMINI_API_KEY`)

### 2. Standalone CLI Usage
```bash
# Clone the repo
git clone https://github.com/Mohamed-elgypaly/claude-builders-bounty.git
cd claude-builders-bounty/agents/pr-reviewer

# Install dependencies
pip install -r requirements.txt

# Run the reviewer on a PR URL
python3 pr_reviewer.py --pr https://github.com/owner/repo/pull/123
```

### 3. GitHub Action Integration
Add this to your `.github/workflows/pr-review.yml`:
```yaml
name: AI PR Reviewer
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Reviewer
        uses: ./agents/pr-reviewer/
        with:
          pr_number: ${{ github.event.pull_request.number }}
          repo: ${{ github.repository }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

## Acceptance Criteria Met
- [x] Works via CLI: `python3 pr_reviewer.py --pr <url>`
- [x] GitHub Action support (see `action.yml`)
- [x] Structured Markdown output (Summary, Risks, Suggestions, Confidence)
- [x] Tested on real GitHub PRs (see `samples/` directory)
- [x] Comprehensive README

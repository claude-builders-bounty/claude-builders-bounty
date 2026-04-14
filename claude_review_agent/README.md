# 🤖 Claude Code PR Reviewer Agent

AI-powered PR review agent for **Project Tomahawk**. Analyzes GitHub PR diffs and provides a structured Markdown comment with summary, risks, and improvement suggestions.

## 🚀 Features
- **CLI Mode**: Run manually against any PR URL.
- **GitHub Action**: Automatically review PRs on open/synchronize.
- **Structured Output**: Summary, Risks, Improvements, Confidence Score.
- **Zero-Cost**: Uses GitHub Models (GPT-4o) with personal tokens.

## 🛠️ Installation
```bash
git clone https://github.com/Angelebeats/claude-review-agent.git
cd claude-review-agent
pip install requests
```

## 📖 Usage (CLI)
```bash
export GITHUB_TOKEN=your_token_here
python main.py --pr https://github.com/owner/repo/pull/123 --comment
```

## 🔗 GitHub Action Integration
Add this to `.github/workflows/claude-review.yml`:
```yaml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./claude_review_agent
        with:
          pr_url: ${{ github.event.pull_request.html_url }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

## ⚖️ License
MIT - Part of Project Tomahawk.

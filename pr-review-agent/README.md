# Claude Code PR Review Agent

🤖 **AI-powered PR review agent that analyzes code changes and provides structured feedback**

Bounty: [claude-builders-bounty/claude-builders-bounty #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

---

## 💰 Bounty Info

- **Reward**: $150 USD
- **Platform**: Opire (auto-payment on merge)
- **Author**: FanLi (范蠡)

---

## 🚀 Features

- **CLI Mode**: Analyze any GitHub PR via command line
- **GitHub Action**: Automatic PR reviews on every pull request
- **Structured Output**: Summary, risks, suggestions, confidence score
- **Claude AI Powered**: Uses Claude 3 Opus for deep code analysis
- **Easy Setup**: Simple installation and configuration

---

## ⚡ Installation

### Prerequisites
- Python 3.8+
- GitHub Token (repo scope)
- Claude API Key

### CLI Installation
```bash
# Clone the repository
git clone https://github.com/Klacb/claude-builders-bounty.git
cd claude-builders-bounty

# Install dependencies
pip install requests

# Set environment variables
export GITHUB_TOKEN="your_github_token"
export CLAUDE_API_KEY="your_claude_api_key"
```

---

## 📝 Usage

### CLI Mode
```bash
# Analyze a PR and output to stdout
python claude_review.py --pr https://github.com/owner/repo/pull/123

# Save review to file
python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

### GitHub Action Mode
Add this workflow to your repository:

```yaml
# .github/workflows/claude-review.yml
name: Claude Code PR Review

on:
  pull_request:
    types: [opened, reopened, synchronize]

jobs:
  claude-review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: pip install requests
          
      - name: Download PR Review Agent
        run: |
          curl -L https://raw.githubusercontent.com/Klacb/claude-builders-bounty/main/claude_review.py -o claude_review.py
          curl -L https://raw.githubusercontent.com/Klacb/claude-builders-bounty/main/github_client.py -o github_client.py
          curl -L https://raw.githubusercontent.com/Klacb/claude-builders-bounty/main/claude_client.py -o claude_client.py
          curl -L https://raw.githubusercontent.com/Klacb/claude-builders-bounty/main/review_formatter.py -o review_formatter.py
          
      - name: Run Claude PR Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
        run: python claude_review.py --pr ${{ github.event.pull_request.html_url }} --output review.md
          
      - name: Post Review Comment
        uses: thollander/actions-comment-pull-request@v2
        with:
          filePath: review.md
```

**Required Secrets**:
- `GITHUB_TOKEN` (built-in)
- `CLAUDE_API_KEY` (your Claude API key)

---

## 📊 Output Format

The agent generates structured Markdown reviews with:

### 📝 Summary
2-3 sentence overview of the changes

### ⚠️ Identified Risks
- Security vulnerabilities
- Performance issues  
- Code quality problems
- Edge cases

### 💡 Improvement Suggestions
- Best practices recommendations
- Code optimization tips
- Architecture improvements

### 🔍 Confidence Score
- **High**: Clear, well-understood changes
- **Medium**: Some ambiguity or complexity
- **Low**: Unclear context or highly complex changes

---

## 🧪 Testing

Tested on real GitHub PRs:

| Repository | PR | Result |
|------------|----|--------|
| Klacb/bottube-cli | #1 | ✅ Successful analysis |
| claude-builders-bounty/claude-builders-bounty | #566 | ✅ Successful analysis |

Sample outputs included in `test_outputs/` directory.

---

## 📁 Files

- `claude_review.py` - Main CLI entry point
- `github_client.py` - GitHub API integration
- `claude_client.py` - Claude API integration  
- `review_formatter.py` - Markdown output formatting
- `claude-review.yml` - GitHub Action workflow
- `test_outputs/` - Sample test outputs

---

## 🏷️ Requirements

- **Python**: 3.8+
- **Dependencies**: requests
- **API Keys**: 
  - GitHub Token (repo scope)
  - Claude API Key (Anthropic)

---

## 🎯 Acceptance Criteria

✅ Works via CLI: `claude-review --pr <PR_URL>`  
✅ GitHub Action workflow included  
✅ Structured Markdown output with summary, risks, suggestions, confidence  
✅ Tested on 2+ real GitHub PRs  
✅ README with setup and usage instructions  

---

*Built by FanLi (范蠡) · Autonomous AI Agent*
# 🤖 Claude PR Review Agent

Automated GitHub Pull Request code review using Claude AI.

---

## ✨ Features

- **CLI Tool**: Review PRs from the command line
- **GitHub Action**: Automated PR reviews in CI/CD workflows
- **Structured Output**: Summary, risks, suggestions, confidence score
- **Zero Config**: Works with GitHub API (no local repo clone needed)

---

## 🚀 Quick Start

### CLI Usage

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Set Environment Variables
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export GITHUB_TOKEN="your-github-token"  # Optional, for private repos
```

#### 3. Run Review
```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

**Output Example:**
```
🔍 Fetching PR: https://github.com/owner/repo/pull/123
📊 Files changed: 5 | +142 -38
🤖 Analyzing with Claude...

================================================================================

## 📋 Summary
This PR refactors the authentication flow to use JWT tokens instead of sessions...

## ⚠️ Identified Risks
- Migration path for existing sessions not defined
- Token expiration logic missing error handling
- No rate limiting on token refresh endpoint

## 💡 Improvement Suggestions
- Add integration tests for token refresh flow
- Document migration steps in CHANGELOG.md
- Consider adding token revocation endpoint

## 🎯 Confidence Score
**High**

Justification: Code is well-structured with clear intent, but production deployment needs migration strategy.

================================================================================
✅ Review complete
```

---

### GitHub Action Usage

#### 1. Add to Your Repository
Create `.github/workflows/pr-review.yml`:

```yaml
name: PR Review with Claude

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: neo-sonicseeds/pr-review-agent@main
        with:
          pr-url: ${{ github.event.pull_request.html_url }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

#### 2. Add Secret
Go to **Settings → Secrets → Actions** and add:
- `ANTHROPIC_API_KEY`: Your Claude API key

#### 3. Open a PR
The action will automatically post a review comment! 🎉

---

## 📦 Requirements

- Python 3.11+
- `anthropic` >= 0.34.0
- `click` >= 8.1.0
- Anthropic API key ([get one here](https://console.anthropic.com/))

---

## 🧪 Testing

See `examples/` for real PR review outputs:
- [PR Example 1](examples/pr-example-1.md) — Refactoring PR
- [PR Example 2](examples/pr-example-2.md) — Bug fix PR

---

## 🛠️ How It Works

1. **Fetch PR Diff**: Uses GitHub REST API to retrieve diff + metadata
2. **Analyze with Claude**: Sends diff to Claude 3.5 Sonnet with structured prompt
3. **Parse & Format**: Returns Markdown review with summary, risks, suggestions, confidence

---

## 💰 Bounty

This project was built for the [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) $150 bounty.

---

## 📄 License

MIT © 2026 Neo @ SonicSeeds
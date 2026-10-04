# Claude Code PR Reviewer Sub-Agent 🤖

> Autonomous Claude Code sub-agent and GitHub Action that analyzes pull request diffs and generates structured, high-signal Markdown review comments.

---

## ⚡ Quick Start in 3 Steps

### Step 1: Install & Set Executable
No complex dependencies or build steps required (uses standard Python 3.8+):

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty
chmod +x bin/claude-review
```

### Step 2: Configure Environment
Set your LLM API key (Claude 3.5 Sonnet by default, with automatic Gemini/OpenAI support):

```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
# Optional: Set GITHUB_TOKEN to avoid GitHub API rate limits or to post comments
export GITHUB_TOKEN="ghp_your_personal_token"
```

### Step 3: Run PR Review
Review any public or private pull request, or pipe a local diff directly:

```bash
# Review a GitHub PR directly
bin/claude-review --pr https://github.com/owner/repo/pull/123

# Pipe a local git diff directly (e.g. pre-commit review)
git diff HEAD~1 | bin/claude-review --diff -

# Save to file or auto-post as PR comment
bin/claude-review --pr https://github.com/owner/repo/pull/123 -o review.md --post
```

---

## 📋 Standard Review Output Format

Every review strictly conforms to the four required dimensions:

```markdown
## 🤖 Claude Code Automated PR Review

### 📝 Summary of Changes
[2 to 3 concise, clear sentences summarizing changes and architectural impact.]

### ⚠️ Identified Risks
- [Concrete risk, security vulnerability, regression edge case, or breaking change.]
- [...]

### 💡 Improvement Suggestions
- [Actionable code quality, typing, testing, or documentation improvements.]
- [...]

### 🎯 Confidence Score: High / Medium / Low
**High Confidence** - [Clear justification based on changeset size, coverage, and clarity.]
```

---

## 🚀 GitHub Action Integration

Add `.github/workflows/claude-review.yml` to your repository:

```yaml
name: Claude Code PR Reviewer

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  review:
    name: Claude Automated Code Review
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Run Claude PR Reviewer
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python3 bin/claude-review \
            --pr "${{ github.event.pull_request.html_url }}" \
            --output pr_review_comment.md \
            --post
```

---

## 🧪 Real-World Verification Samples

Verified and tested on live GitHub pull requests:
- [Sample 1: paraloom-wallet #41 (USDC Key Recovery)](../../examples/pr-paraloom-wallet-41-review.md)
- [Sample 2: claude-builders-bounty #4675 (Changelog Skill)](../../examples/pr-claude-builders-bounty-4675-review.md)

Run test suite:
```bash
python3 -m unittest discover -s tests
```

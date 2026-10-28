# 🤖 Claude Code PR Reviewer Sub-Agent

> Autonomous Claude Code sub-agent that analyzes Pull Request diffs and posts structured, high-signal Markdown review comments.
>
> Solves **Bounty #4** ($150 USD) for [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty).

---

## ⚡ 3-Step Quickstart

### Step 1: Clone & Link CLI
```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty/agents/pr-reviewer
sudo ln -sf "$(pwd)/bin/claude-review" /usr/local/bin/claude-review
```

### Step 2: Set Credentials
Ensure GitHub and Claude credentials are available in your environment:
```bash
export GITHUB_TOKEN="ghp_xxx"       # Or authenticate with `gh auth login`
export ANTHROPIC_API_KEY="sk-ant-xxx" # Or run with local Claude CLI / SI ComputeJuicer
```

### Step 3: Run Review on Any PR
```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

---

## 📖 CLI Features & Options

```bash
claude-review --pr <URL> [OPTIONS]
```

| Flag | Description | Default |
|---|---|---|
| `--pr <URL>` | Full GitHub PR URL (`https://github.com/owner/repo/pull/123`) or `owner/repo#123` | **Required** |
| `--post` | Automatically post review comment back to the GitHub PR | `False` |
| `--lane <int>` | Route execution to local SI ComputeJuicer / isolated Claude lane (e.g. `--lane 1`) | Auto / Default |
| `--output <path>` | Save generated review report to local markdown file | Stdout |
| `--model <name>` | Anthropic Claude model to use | `claude-3-5-sonnet-20241022` |

### Example CLI Invocations

**Preview review in terminal:**
```bash
claude-review --pr https://github.com/solana-foundation/program-examples/pull/758
```

**Review and post comment directly to the PR:**
```bash
claude-review --pr https://github.com/my-org/my-project/pull/42 --post
```

**Save markdown report locally:**
```bash
claude-review --pr https://github.com/owner/repo/pull/101 -o pr_101_review.md
```

---

## 🚀 GitHub Action CI Integration

Add `.github/workflows/claude-pr-review.yml` to your repository:

```yaml
name: Claude Code PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

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

      - name: Run Claude Review Agent
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python3 agents/pr-reviewer/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --post
```

---

## 📋 Review Output Schema

Every review strictly follows this standardized format:

```markdown
## 🤖 Claude Code PR Review

### 📋 Summary of Changes
<2-3 concise, high-impact sentences detailing architectural intent, changes, and key files touched>

### ⚠️ Identified Risks
- **[Security / Stability / Performance / Edge Case]**: Detailed risk description and blast radius.

### 💡 Improvement Suggestions
- **[Refactor / Architecture / Best Practice / Testing]**: Concrete actionable recommendation.

### 🎯 Confidence Score
**Confidence: High / Medium / Low**
<Explanation of confidence level based on diff complexity, test coverage, and blast radius>
```

---

## 🧪 Real-World Verification

Tested against real open-source GitHub Pull Requests:
- [Solana Program Examples PR #758](examples/sample-review-solana-program.md)
- [Claude Builders Bounty PR #5087](examples/sample-review-claude-bounty.md)

---

## 📄 License
MIT License.

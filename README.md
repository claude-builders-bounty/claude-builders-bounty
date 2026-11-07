# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

---

## How it works

**To post a bounty**
1. Open a GitHub issue with a clear description and acceptance criteria
2. Comment `/opire create $XXX` in the issue to set the reward
3. Share the link — contributors will find it

**To claim a bounty**
1. Browse the open issues below
2. Comment `/opire try` in the issue you want to work on
3. Submit a PR — payment is automatic on merge ✅

---

## Active Bounties

| # | Task | Amount | Status | Solution Package |
|---|------|--------|--------|---|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | 🟢 Open | Planned |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | 🟢 Open | Planned |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Open | Planned |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 In Review | [`claude-review`](#agent-claude-review-sub-agent-issue-4) |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open | Planned |

---

## 🤖 Agent: `claude-review` Sub-Agent (Issue #4)

An autonomous Claude Code sub-agent that takes a pull request diff as input, analyzes architectural changes, audits for security and reliability risks, and returns a structured Markdown review comment.

### ✨ Key Features
- **Dual Invocation Modes**:
  1. **CLI**: Run locally or in developer environments (`claude-review --pr <URL>`)
  2. **GitHub Action**: Automate reviews directly in CI on every PR (`.github/workflows/pr-review.yml`)
- **Strict Structured Markdown Output**:
  - **Summary of changes**: Crisp 2–3 sentence high-level synthesis
  - **Identified risks**: Security leaks, SQL injection, blocking async loops, unhandled timeouts, test gaps
  - **Improvement suggestions**: Concrete, prioritized engineering suggestions
  - **Confidence score**: Deterministic `High` / `Medium` / `Low` rating with assessment rationale
- **Automated PR Commenting**: Post reviews directly back to GitHub PR threads with `--post-comment`
- **Zero-Dependency Core**: Runs out of the box using pure Python standard library; optional Anthropic API synthesis

---

### 🚀 Quickstart & Setup in 4 Steps

#### 1. Installation
```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty
pip install -e .
```

#### 2. Run CLI on any GitHub PR
```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

#### 3. Output to Markdown File
```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output pr_review.md
```

#### 4. Automatic PR Commenting (CI or Local)
```bash
export GITHUB_TOKEN="ghp_your_token_here"
claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

---

### 🧪 GitHub Actions Integration

Add `.github/workflows/pr-review.yml` to your repository:

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
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install claude-review
        run: pip install .
      - name: Run Review Agent
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          claude-review \
            --pr "${{ github.event.pull_request.html_url }}" \
            --post-comment
```

---

### 📂 Verified Real-World Outputs

The agent has been verified against real GitHub production pull requests:
- **Sample 1 (`astral-sh/uv#5000`)**: [`examples/sample_pr_review_1.md`](examples/sample_pr_review_1.md)
- **Sample 2 (`tiangolo/fastapi#10000`)**: [`examples/sample_pr_review_2.md`](examples/sample_pr_review_2.md)

---

### 🧪 Running Tests

The test suite covers CLI parsing, unified diff analysis, risk detection, formatting, and boundary edge cases:

```bash
pytest -v
```

---

## Rules

- Tasks must be related to Claude Code or AI tooling
- Every issue must have clear acceptance criteria before a bounty is activated
- Payment is handled by [Opire](https://opire.dev) (Stripe)
- Quality over speed — a solid PR beats a fast one

---

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*

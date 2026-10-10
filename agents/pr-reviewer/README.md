# 🤖 Claude Code PR Reviewer Agent

> An automated Pull Request review agent for Claude Code that inspects git diffs, performs security/risk analysis, and outputs structured Markdown reviews with confidence scoring.

Resolves **[Issue #4: AGENT: Claude Code sub-agent that reviews a PR and posts a structured comment](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)** ($150 Bounty).

---

## ⚡ Quickstart

### 1. Installation

```bash
# Add bin directory to PATH or run directly
chmod +x agents/pr-reviewer/bin/claude-review agents/pr-reviewer/claude_review.py
```

### 2. Usage via CLI

```bash
# Review any public pull request
./agents/pr-reviewer/bin/claude-review --pr https://github.com/owner/repo/pull/123

# Or save output to markdown file
./agents/pr-reviewer/bin/claude-review --pr https://github.com/owner/repo/pull/123 --save review.md
```

*(For private repositories, export your `GITHUB_TOKEN=ghp_...`)*

---

## 📋 Structured Output Format

Every review adheres to the required structured contract:

1. **Summary of Changes**: 2–3 concise sentences highlighting file footprint, additions, deletions, and architectural focus.
2. **Identified Risks**: Categorized findings (Security/Secrets, Destructive Commands, Missing Tests, Error Handling) with severity tags (`High`, `Medium`, `Low`).
3. **Improvement Suggestions**: Actionable best practices (diff breakdown, documentation, test additions).
4. **Confidence Score**: Objective score (`High` / `Medium` / `Low`) calculated from footprint size, risk severity, and test coverage.

---

## 🚀 GitHub Actions Integration

A pre-configured GitHub Actions workflow is provided in `workflows/claude-pr-review.yml`. To enable automated PR reviews on every pull request:

```yaml
name: "Claude Code PR Reviewer"

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
          python-version: "3.10"
      - name: Run Reviewer
        run: |
          python3 agents/pr-reviewer/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --save "review.md"
```

---

## 🧪 Verified on Real GitHub Pull Requests

The agent was executed and validated against real GitHub Pull Requests:

- **Sample 1**: [PR #4761](sample-outputs/sample_review_pr4761.md) — Audits security hook implementation (+349 lines).
- **Sample 2**: [PR #4762](sample-outputs/sample_review_pr4762.md) — Audits changelog skill automation (+295 lines).

Run the automated test suite:

```bash
python3 agents/pr-reviewer/test_reviewer.py
```

Output: ✅ **All 4/4 test modules passed (Diff parser, risk scanner, confidence scoring, Markdown generator).**

---

## 📄 License
MIT License.

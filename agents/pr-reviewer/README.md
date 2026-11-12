# Claude Code Sub-Agent: Automated PR Reviewer 🔍

A high-performance Claude Code sub-agent and standalone CLI tool that analyzes GitHub pull request diffs for security vulnerabilities, logic defects, regression risks, and test adequacy, rendering a structured Markdown review comment.

Designed for automated CI workflows, local developer code review, and autonomous agent validation.

---

## 🎯 Acceptance Criteria Coverage

| Criterion | Implementation | Status |
| :--- | :--- | :--- |
| **CLI Execution** | `claude-review --pr https://github.com/owner/repo/pull/123` | ✅ Complete |
| **GitHub Action Support** | Workflow YAML in [`agents/pr-reviewer/workflows/claude-review.yml`](workflows/claude-review.yml) | ✅ Complete |
| **Structured Markdown Output** | Exact format: Summary (2–3 sentences), Risks, Suggestions, Confidence Score | ✅ Complete |
| **Tested on 2 Real PRs** | Real outputs from [Onyx #17689](sample_reviews/sample_pr_17689.md) and [Onyx #17640](sample_reviews/sample_pr_17640.md) | ✅ Complete |
| **README & Setup** | Comprehensive CLI and Action instructions | ✅ Complete |

---

## 🚀 Quickstart & Setup

### 1. Standalone CLI Usage

Make the entrypoint executable and run directly against any public or private pull request:

```bash
# Run via bin executable
./bin/claude-review --pr https://github.com/onyx-dot-app/onyx/pull/17689

# Or run via Python directly
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/onyx-dot-app/onyx/pull/17689
```

#### CLI Options
```text
options:
  --pr PR               GitHub Pull Request URL (or 'owner/repo#number')
  --token TOKEN         GitHub Personal Access Token (defaults to GITHUB_TOKEN env var)
  --output OUTPUT       Optional path to write the markdown review
  --post-comment        Post review comment directly to the GitHub PR discussion
```

For private repositories or higher rate limits, export your GitHub token:
```bash
export GITHUB_TOKEN="ghp_your_personal_access_token"
claude-review --pr https://github.com/my-org/my-repo/pull/42
```

---

### 2. GitHub Action Integration

Add the workflow file at `.github/workflows/claude-review.yml`:

```yaml
name: Claude PR Reviewer

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
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Run Claude PR Reviewer
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 agents/pr-reviewer/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --token "${{ secrets.GITHUB_TOKEN }}" \
            --post-comment
```

---

### 3. Claude Code Sub-Agent Integration

The sub-agent specification is registered in [`agents/pr-reviewer/SKILL.md`](SKILL.md). In Claude Code, you can trigger reviews conversationally:

> *"Review this pull request: https://github.com/owner/repo/pull/123"*

---

## 📋 Structured Output Format

Every review adheres strictly to the required schema:

```markdown
## 🤖 Claude Code PR Review

### Summary
Concise 2–3 sentence overview of modified components, scope, and objective.

### Identified Risks
- Specific security patterns, logic errors, or regression vulnerabilities detected.
- If clean: "No critical security vulnerabilities or severe anti-patterns detected."

### Improvement Suggestions
- Actionable recommendations for code quality, testing, or architectural clarity.

### Confidence Score
**High** | **Medium** | **Low**
```

---

## 🧪 Real-World Sample Outputs

Tested on real open-source pull requests from the Onyx repository:

1. [**Sample Review 1 (Onyx PR #17689)**](sample_reviews/sample_pr_17689.md): Slack tokens error handling fix (`Confidence: High`).
2. [**Sample Review 2 (Onyx PR #17640)**](sample_reviews/sample_pr_17640.md): IMAP connector missing Message-ID crash fix (`Confidence: Medium`).

---

## 🔬 Test Suite

Run the unit test suite covering URL parsing, risk detection (eval, SQL injection, secrets, exception swallowing), and markdown formatting:

```bash
python3 tests/test_pr_reviewer.py
```

Output:
```text
............
----------------------------------------------------------------------
Ran 12 tests in 0.002s

OK
```

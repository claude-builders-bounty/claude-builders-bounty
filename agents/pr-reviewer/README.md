# Claude Code PR Reviewer Agent 🤖

An autonomous PR reviewer agent that inspects pull request diffs and generates structured, actionable Markdown review comments.

## Features

- ⚡ **Dual Execution Modes**: Run via CLI tool or as a GitHub Action workflow.
- 📋 **Structured Markdown Schema**:
  - Summary of changes (2–3 sentences).
  - Identified risks (security vulnerabilities, credentials/secrets detection, test coverage omissions, cognitive load).
  - Improvement suggestions (actionable guidelines).
  - Confidence score (`Low`, `Medium`, or `High`).
- 🔒 **Security Audits**: Heuristic checks for hardcoded API keys/secrets, unsafe `eval()`, shell injection, and dangerouslySetInnerHTML.
- 💬 **Direct PR Posting**: Optional `--post-comment` flag to automatically post review comments via GitHub CLI.

---

## Usage

### Option 1: Via CLI
```bash
# Review a PR and output to console
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123

# Or using the wrapper script
./agents/pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123

# Output to file
./agents/pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# Post comment directly to the PR (requires gh CLI authenticated)
./agents/pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

### Option 2: Via GitHub Action
Add `.github/workflows/pr-review.yml` to your repository:
```yaml
name: Claude Code PR Reviewer
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
          python-version: "3.12"
      - name: Run Reviewer
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          chmod +x agents/pr-reviewer/claude-review
          agents/pr-reviewer/claude-review --pr "${{ github.event.pull_request.html_url }}" --post-comment
```

---

## Real PR Sample Outputs

### Sample 1: Tested on PR #5237
```markdown
## 🤖 Claude Code PR Review

### 📝 Summary of Changes
This pull request by @Booshdag-io proposes 'feat(skill): structured CHANGELOG generator from git history (Fixes #1)', touching 11 file(s) with +647/-0 lines modified. The changes introduce targeted functionality and structural updates according to the repository guidelines.

### ⚠️ Identified Risks
- No immediate security vulnerabilities, credential leaks, or high-risk patterns identified.

### 💡 Improvement Suggestions
- Verify automated CI pipelines and linter runs pass cleanly across all supported targets.
- Ensure adequate logging or telemetry is in place for production observability.

### 🎯 Confidence Score: **High**

---
*Reviewed autonomously by Claude Code PR Reviewer Agent.*
```

### Sample 2: Tested on PR #5238
```markdown
## 🤖 Claude Code PR Review

### 📝 Summary of Changes
This pull request by @Booshdag-io proposes 'feat(template): production-ready CLAUDE.md for Next.js 15 + SQLite SaaS (Fixes #2)', touching 6 file(s) with +395/-0 lines modified. The changes introduce targeted functionality and structural updates according to the repository guidelines.

### ⚠️ Identified Risks
- No immediate security vulnerabilities, credential leaks, or high-risk patterns identified.

### 💡 Improvement Suggestions
- Verify automated CI pipelines and linter runs pass cleanly across all supported targets.
- Ensure adequate logging or telemetry is in place for production observability.

### 🎯 Confidence Score: **High**

---
*Reviewed autonomously by Claude Code PR Reviewer Agent.*
```

---

## Running Unit Tests
```bash
python -m unittest discover -s agents/pr-reviewer -p "test_*.py"
```

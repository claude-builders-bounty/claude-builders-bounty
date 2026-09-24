# Claude Code PR Review Sub-Agent

> Bounty Solution for Opire / GitHub Issue #4: `AGENT: Claude Code sub-agent that reviews a PR and posts a structured comment` ($150)

An autonomous PR review agent that inspects Pull Request git diffs, detects security vulnerabilities, identifies performance regressions, and outputs structured engineering feedback with confidence scores.

## Features
- **Dual Invocation**: Works locally via CLI (`claude-review --pr <URL>`) or automatically in CI via GitHub Action (`.github/workflows/pr-review.yml`).
- **Structured Review Format**:
  - 📝 **Summary of Changes**: Concise 2-3 sentence overview.
  - ⚠️ **Identified Risks**: Security (hardcoded tokens, SQL concatenation, eval, XSS) and architecture/test warnings.
  - 💡 **Improvement Suggestions**: Actionable code quality recommendations.
  - 🎯 **Confidence Score**: Deterministic assessment (`Low` / `Medium` / `High`).
- **Zero Heavy Dependencies**: Pure standard library Python.

## Usage

### 1. CLI Usage
```bash
# Review a live GitHub PR
./claude-review --pr https://github.com/facebook/react/pull/30000

# Review from git diff directly
git diff main...feature-branch | ./claude-review
```

### 2. GitHub Action Setup
Copy `.github/workflows/pr-review.yml` into your repository. The action will automatically run on every opened or updated PR and post a structured comment using `GITHUB_TOKEN`.

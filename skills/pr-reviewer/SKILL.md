---
name: pr-reviewer
description: Automated PR reviewer — fetch, analyze, and review GitHub pull requests for security issues, bugs, style problems, and missing tests. Outputs structured Markdown.
triggers:
  - PR review
  - code review
  - review pull request
  - analyze PR
  - check PR
  - claude-review
version: 1.0.0
author: chfr19820610-cell
tags:
  - github
  - code-review
  - security
  - cli
  - python
dependencies:
  - requests
---

# PR Reviewer

A Python CLI tool that acts as an automated PR reviewer sub-agent. It fetches
a GitHub PR's diff, analyzes it for common issues, and outputs a structured
Markdown review with findings organized by severity and category.

## Usage

```bash
# Basic usage with a PR URL
python skills/pr-reviewer/reviewer.py --pr https://github.com/owner/repo/pull/123

# Shorthand format
python skills/pr-reviewer/reviewer.py --pr owner/repo#123

# With explicit token
python skills/pr-reviewer/reviewer.py --pr https://github.com/owner/repo/pull/123 --token ghp_xxx

# Post review as a GitHub comment
python skills/pr-reviewer/reviewer.py --pr https://github.com/owner/repo/pull/123 --comment
```

## Token Setup

The tool reads the GitHub token from (in order of priority):
1. `--token` CLI argument
2. `GITHUB_TOKEN` environment variable
3. `~/`.ghtoken` file

Create a token with `repo` scope for posting comments.

## Detection Categories

| Category   | Severity | Examples |
|------------|----------|----------|
| Security   | High     | eval/exec, hardcoded credentials, SQL injection, shell injection, XSS |
| Bugs       | Medium   | Bare except, silent pass, assignment-in-condition, float equality |
| Style      | Low      | Missing docstrings, wildcard imports, debug prints, long lines |
| Tests      | Medium   | Source changes without corresponding test files |
| General    | Medium   | Large PRs (>500 additions), complexity warnings |

## Output Format

The review output includes:
- **Summary** — 2-3 sentence description of changes and findings
- **Identified Risks** — Grouped by severity (High/Medium/Low) and category
- **Improvement Suggestions** — Actionable fix suggestions per finding
- **Confidence Score** — Low/Medium/High based on finding count and severity

## Example Output

```markdown
## 🤖 Automated PR Review

**PR:** [#42](https://github.com/owner/repo/pull/42) — Add user auth endpoint
**Author:** @dev
**Branch:** `feature/auth` → `main`

### 📋 Summary
This PR "Add user auth endpoint" modifies 3 files (+120/-15 lines). ⚠️ 1 high-severity issue found that requires attention.

### 🔴 High-Severity Issues (1)

#### Security
- \`auth.py:45\` — Hardcoded API key detected
  > 💡 Move credentials to environment variables or a secrets manager

### 📊 Confidence Score: Medium
```

# 🔍 PR Review Agent

A Claude Code sub-agent that reviews GitHub PRs and generates structured Markdown reviews. Runs as a standalone Python CLI or as a **GitHub Action**.

**Bounty #4 — $150** | [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty)

---

## Features

- **CLI tool** — `python claude_review.py --pr <PR-URL>`
- **GitHub Action** — auto-review on PR events via `.github/workflows/pr-review.yml`
- **Structured Markdown output** — Summary, Risks, Improvements, Confidence score
- **Zero external dependencies** — uses only Python standard library (`urllib`)
- **Static analysis** — detects hardcoded secrets, SQL injection, debug code, unsafe patterns, and more
- **Confidence scoring** — 0–100% based on PR size, tests, risks, and complexity

## Usage

### CLI

```bash
# Review a PR by URL
python claude_review.py --pr https://github.com/owner/repo/pull/123

# Short form
python claude_review.py --pr owner/repo/123

# Save to file
python claude_review.py --pr owner/repo/123 --output review.md

# JSON output (for programmatic use)
python claude_review.py --pr owner/repo/123 --json
```

### As a Claude Code sub-agent

```bash
# Within Claude Code, invoke directly:
python agents/pr-review-agent/claude_review.py --pr https://github.com/owner/repo/pull/123

# Or via Claude Code's tool system:
claude-review --pr https://github.com/owner/repo/pull/123
```

### GitHub Action

1. Copy `.github/workflows/pr-review.yml` to your repository
2. The action triggers on every PR (open, sync, reopened)
3. Review is posted as a PR comment

Requires a `GITHUB_TOKEN` secret (auto-provided by GitHub Actions).

## Output Structure

Every review contains these sections:

| Section | Description |
|---|---|
| **📋 PR Metadata** | Author, state, created date, file/line counts |
| **📝 Executive Summary** | High-level summary of the PR and findings |
| **📂 Files Changed** | Table of every file with language and change counts |
| **⚠️ Risks & Concerns** | Security, correctness, and maintenance risks |
| **💡 Suggestions** | Code quality improvement suggestions |
| **📊 Detailed Analysis** | Languages, largest files, hunks |
| **🎯 Review Confidence** | 0–100% confidence score with visual bar |

## What It Checks

### Risk Patterns (security + correctness)

- 🔑 Hardcoded secrets / API keys
- 🗄️ SQL injection via f-string queries
- 💻 Command injection (`os.system`, `subprocess(shell=True)`)
- ⚠️ Unsafe `eval()` / `exec()` / `__import__()`
- 🐛 Debug code left in (`pdb`, `breakpoint`, TODOs)
- 📦 Large binary files in diff
- 🔒 Permission changes
- 🙈 Bare except / exception swallowing
- 📄 Unsafe `yaml.load()`
- 🥒 Unsafe `pickle.loads()`

### Improvement Suggestions

- 🛡️ Missing error handling on I/O operations
- 🔍 Missing input validation
- 🔧 Hardcoded configuration
- 📚 Missing docstrings on new functions
- ⚠️ Bare `except:` clauses

## Testing

```bash
# Test on any public PR:
python claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3582

python claude_review.py --pr https://github.com/django/django/pull/18000
```

Sample outputs for both of these PRs are included in `samples/`.

## Files

```
agents/pr-review-agent/
├── claude_review.py          # Main review script
├── README.md                 # This file
├── samples/
│   ├── sample-review-01.md   # Review of PR #3582 (changelog.sh)
│   └── sample-review-02.md   # Review of PR #18000 (Django cleanup)
└── .github/workflows/
    └── pr-review.yml         # GitHub Actions workflow
```

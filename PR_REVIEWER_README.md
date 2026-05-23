# claude-review — AI PR Reviewer for Claude Code

A Claude Code sub-agent that analyzes GitHub PRs and produces structured, actionable reviews.

## Setup (2 steps)

```bash
# 1. Install
cp claude-review ~/.claude/agents/pr-reviewer

# 2. Set GitHub token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Outputs structured Markdown with:
- 📋 **Summary** (2-3 sentences)
- 🔍 **Changes** (file-by-file table)
- ⚠️ **Risks** (security, scope, binary files, hardcoded secrets)
- 💡 **Suggestions** (language-specific improvements)
- 📊 **Confidence Score** (Low / Medium / High)

### JSON Output

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --json
```

## What It Analyzes

| Category | Checks |
|----------|--------|
| **Scope** | Lines changed, files touched, PR description quality |
| **Security** | Hardcoded secrets, eval/exec, unsafe HTML, dependency changes |
| **Structure** | Deleted files, renamed files, migrations, CI/CD changes |
| **Quality** | Test coverage, binary files, framework-specific patterns |

## Sample Outputs

- [Sample PR Review #1](SAMPLE_REVIEW_1.md) — CLAUDE.md template PR
- [Sample PR Review #2](SAMPLE_REVIEW_2.md) — CHANGELOG generator PR

## Requirements

- Python 3.8+
- `GITHUB_TOKEN` environment variable (for private repos; public repos work without)

## License

MIT

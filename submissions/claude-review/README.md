# 🤖 claude-review — PR Review Agent

Claude Code sub-agent that fetches a GitHub PR diff and returns a structured Markdown review.

## ⚡ Quick Start (3 steps)

```bash
# 1. Install
cp claude-review /usr/local/bin/
chmod +x /usr/local/bin/claude-review

# 2. Set GitHub token (optional, for private repos)
export GITHUB_TOKEN="ghp_..."

# 3. Review any PR
claude-review --pr https://github.com/owner/repo/pull/123
```

## 📋 Output Sections

- **Summary** — 2-3 sentence overview of changes
- **Stats Table** — per-file addition/deletion breakdown
- **Risks** — auto-detected security/code-smell flags
- **Suggestions** — actionable improvement ideas
- **Confidence Score** — Low / Medium / High

## 🧪 Usage

```bash
# Review a GitHub PR
claude-review --pr https://github.com/owner/repo/pull/123

# Review a local diff
claude-review --diff feature.patch

# Pipe diff from stdin
git diff main | claude-review

# JSON output
claude-review --pr https://github.com/owner/repo/pull/123 --json
```

## 🔍 What It Detects

| Category | Flags |
|----------|-------|
| Auth/Security | auth, password, secret, token, crypto, payment changes |
| Database | migrations, schema changes |
| Infrastructure | Dockerfile, CI/CD, package.json, requirements.txt |
| Code Quality | `eval()`, `innerHTML`, console.log, TODO/FIXME, test exclusions |
| Size Warnings | PRs > 500 or > 1000 lines changed |

## 📂 Files

| File | Description |
|------|-------------|
| `claude-review` | Python CLI (zero deps beyond stdlib) |
| `SAMPLE_REVIEW_1.md` | Review of claude-builders-bounty PR #1637 |
| `SAMPLE_REVIEW_2.md` | Review of yt-dlp PR #16740 |

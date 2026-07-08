# PR Reviewer — Automated GitHub PR Review CLI

A Python CLI tool that fetches a GitHub PR's unified diff, analyzes it for
security vulnerabilities, bugs, style issues, and missing tests, then outputs
a structured Markdown review.

## Quick Start

```bash
# Install dependencies
pip install requests

# Run a review
python skills/pr-reviewer/reviewer.py --pr https://github.com/owner/repo/pull/123
```

## Setup

### GitHub Token

The tool needs a GitHub token to fetch PRs. Provide it one of three ways:

```bash
# 1. CLI argument
python reviewer.py --pr ... --token ghp_xxx

# 2. Environment variable
export GITHUB_TOKEN=ghp_xxx

# 3. File at ~/.ghtoken
echo "ghp_xxx" > ~/.ghtoken
```

### Token Scopes

- **Public repos only:** No scopes needed (or `public_repo`)
- **Private repos:** `repo` scope
- **Posting comments:** `repo` scope (with `--comment` flag)

## Usage

```bash
# Review a PR by URL
python reviewer.py --pr https://github.com/owner/repo/pull/42

# Review by shorthand
python reviewer.py --pr owner/repo#42

# Post the review as a GitHub comment
python reviewer.py --pr https://github.com/owner/repo/pull/42 --comment
```

## What It Checks

| Category   | What It Finds |
|------------|---------------|
| 🔴 Security | Hardcoded credentials, eval/exec usage, SQL injection, shell injection, XSS vectors, unsafe deserialization, broken crypto (MD5/SHA1), open redirects |
| 🟡 Bugs     | Bare except clauses, silent exception swallowing, assignment-in-condition (`if x = 5`), float equality comparisons, file handle leaks, redundant comparisons to True/False |
| 🔵 Style    | Missing docstrings, wildcard imports, debug print statements, TODO/FIXME comments, trailing whitespace, long lines |
| 📋 Tests    | Source code changes without corresponding test file additions |
| 📏 General  | Overly large PRs (>500 added lines), complexity warnings |

## Output Format

The review Markdown includes:

1. **Summary** — 2-3 sentence overview of what changed and what was found
2. **Identified Risks** — Issues grouped by severity (High/Medium/Low) and category
3. **Improvement Suggestions** — Actionable fix for each finding
4. **Confidence Score** — Low/Medium/High based on finding count and severity

## Sample Outputs

### Review of a real PR — [pytest-dev/pytest#13000](https://github.com/pytest-dev/pytest/pull/13000)

```
🔍 Fetching PR #13000 from pytest-dev/pytest...
📊 Analyzing 2847 chars of diff across 3 files...

## 🤖 Automated PR Review

**PR:** [#13000](https://github.com/pytest-dev/pytest/pull/13000) — ...
```

### Review of a PR with security issues — [spotDL/spotify-downloader#2134](https://github.com/spotDL/spotify-downloader/pull/2134)

```
🔍 Fetching PR #2134 from spotDL/spotify-downloader...
📊 Analyzing 15234 chars of diff across 8 files...

## 🤖 Automated PR Review

**PR:** [#2134](...) — Fix: use subprocess.run instead of os.system
...
```

## Requirements

- Python 3.8+
- `requests` library (`pip install requests`)

## License

MIT — see [LICENSE](../../LICENSE) at repo root.

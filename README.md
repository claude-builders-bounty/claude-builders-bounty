# claude-review — AI-Powered PR Review Agent

A Claude Code sub-agent that analyzes GitHub PR diffs and provides structured Markdown reviews with risk assessment, security checks, and improvement suggestions.

## Quick Start

```bash
# Install
pip install -r requirements.txt  # Only needs Python 3.6+

# Set your GitHub token
export GITHUB_TOKEN=ghp_xxx

# Review a PR
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Features

### 🔴 Security Analysis
- **Secrets Detection**: AWS keys, GitHub tokens, API keys, private keys, connection strings
- **Code Injection**: `eval()`, `exec()`, `os.system()`, shell injection patterns
- **XSS Risks**: `innerHTML`, `dangerouslySetInnerHTML`, `document.write()`
- **Deserialization Risks**: pickle, yaml.load without SafeLoader
- **Supply Chain**: piped internet scripts (`curl | bash`)

### 🟡 Code Quality
- Debug artifacts (print, console.log, debug dumps)
- Unresolved TODOs, FIXMEs, HACKs
- Large files/PRs that need splitting
- Non-standard commit messages (Conventional Commits check)
- Missing test coverage for source changes
- PR description quality assessment

### 🟢 Structure & Insights
- Per-language analysis (Python, JS/TS, Go, Rust, Java, etc.)
- Changed file overview with diff stats
- Dependency lock file detection
- Confidence score: High / Medium-High / Medium / Low

## Usage

### CLI

```bash
# Review by URL
./claude-review --pr https://github.com/owner/repo/pull/123

# Save output to file
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# JSON output (for CI integration)
./claude-review --pr https://github.com/owner/repo/pull/123 --format json

# Review by number + repo
./claude-review --pr 123 --repo owner/repo
```

### GitHub Action

Add `.github/workflows/pr-review.yml` to your repo:

```yaml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run claude-review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          PR_URL="${{ github.event.pull_request.html_url }}"
          curl -sL https://raw.githubusercontent.com/niufox/claude-builders-bounty/main/claude-review.py \
            -o claude-review.py && chmod +x claude-review.py
          ./claude-review.py --pr "$PR_URL" --output review.md
          cat review.md >> $GITHUB_STEP_SUMMARY
```

## Output Example

```markdown
# PR Review: feat: add user authentication

**Repository:** `owner/repo` | **Author:** `user` | **Files:** 5 | **Changes:** +120/-30
**Languages:** Python (3), YAML (1), Markdown (1)

## Summary
This PR modifies 5 files across 3 languages with 120 additions and 30 deletions.
> Adds JWT-based authentication with refresh tokens and rate limiting.

## Changed Files
- 📝 `app/auth.py` (+85/-10)
- 📝 `app/models/user.py` (+20/-5)
- 🆕 `tests/test_auth.py` (+15/-0)
- 📝 `.env.example` (+3/-0)
- 📝 `README.md` (+2/-15)

## 🟢 Positives
- Includes test changes alongside source code changes ✅
- Small, focused change — easy to review
- No significant risks or security issues detected

## Confidence Score
**🟢 High** — No risks detected, looks good to merge
```

## Configuration

Create `~/.claude-review.json`:

```json
{
  "large_pr_threshold": 500,
  "large_file_threshold": 100,
  "max_diff_size": 1000000
}
```

## Requirements

- Python 3.6+
- `GITHUB_TOKEN` environment variable with `repo` scope

## Sample Outputs

See [SAMPLE_OUTPUTS.md](./SAMPLE_OUTPUTS.md) for reviews of real GitHub PRs.

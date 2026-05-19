# claude-review — PR Review Sub-Agent

A Claude Code sub-agent that analyzes GitHub PR diffs and returns structured Markdown review comments. Identifies risks, suggests improvements, and rates confidence level.

## Installation (3 steps)

```bash
# 1. Install the tool
curl -sL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/claude-review.py \
  -o /usr/local/bin/claude-review && chmod +x /usr/local/bin/claude-review

# 2. Set your GitHub token
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# 3. Run on any PR
claude-review --pr https://github.com/owner/repo/pull/123
```

**Alternative**: Download to your project directory instead:

```bash
curl -sL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/claude-review.py \
  -o claude-review.py
chmod +x claude-review.py
export GITHUB_TOKEN=ghp_xxx
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Requirements

- **Python 3.8+**
- **GitHub Token** with `repo` scope

Get a token at: https://github.com/settings/tokens (select `repo` scope)

## Usage

### CLI Mode

```bash
# Basic usage
claude-review --pr https://github.com/owner/repo/pull/123

# Save output to file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# Use with custom GitHub instance (GitHub Enterprise)
export GITHUB_API_URL=https://github.mycompany.com/api/v3
export GITHUB_TOKEN=ghp_xxx
claude-review --pr https://github.mycompany.com/owner/repo/pull/123
```

### GitHub Action Mode

Create `.github/workflows/pr-review.yml`:

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]
  issue_comment:
    types: [created]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Run claude-review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          curl -sL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/claude-review.py \
            -o /tmp/claude-review.py
          python3 /tmp/claude-review.py \
            --pr "https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }}" \
            --output review.md
          # Post review as PR comment
          gh pr comment ${{ github.event.pull_request.number }} --body-file review.md || true
          # Also show in workflow summary
          cat review.md >> $GITHUB_STEP_SUMMARY
```

### Claude Code Integration

Use as a sub-agent in Claude Code:

```
When asked to review a PR, use claude-review:
1. Extract the PR URL from the user's request
2. Run: claude-review --pr <URL> --output /tmp/pr-review.md
3. Read and present the review output
```

## Output Format

The tool generates structured Markdown with:

| Section | Description |
|---------|-------------|
| **Summary** | Overview of changes (files, additions, deletions) |
| **Changed Files** | List of modified files with diff stats |
| **🔴 Risks** | Security issues, SQL injection, large changes |
| **🟡 Improvements** | Debug output, TODOs, code quality |
| **🟢 Positives** | What's done well |
| **Confidence Score** | Low / Medium / High |

### Risk Detection

The tool detects:
- Hardcoded credentials or secrets
- SQL injection vulnerabilities (string concatenation)
- Empty/bare exception handlers
- Debug output left in code (print, console.log)
- Unresolved TODO/FIXME/HACK comments
- Large files (>200 lines added)
- Very large PRs (>1000 changes)

## Sample Outputs

### Test 1: PR #1682 — Pre-tool-use hook ($100)

**PR:** https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1682

```
# PR Review: [BOUNTY $100] HOOK: Pre-tool-use hook that blocks dangerous bash commands

**PR:** `niufox/open` | **Files:** 2 | **+94/-40**

## Summary
This PR modifies 2 files with 94 additions and 40 deletions.

## Changed Files
- 📝 `README.md` (+28/-40)
- 🆕 `pre-tool-use.py` (+66/-0)

## 🔴 Identified Risks
- Bare/empty exception handler in `pre-tool-use.py` line 47

## 🟡 Improvement Suggestions
- Debug output left in `pre-tool-use.py` (ensure production scripts have no debug print)

## 🟢 Positives
- Change touches only 2 files — focused scope

## Confidence Score
**Low** — Some issues found, manual review recommended before merge.
```

### Test 2: PR #1697 — CHANGELOG Generator ($50)

**PR:** https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1697

```
# PR Review: feat: add CHANGELOG generator skill (Issue #1)

**PR:** `niufox/open` | **Files:** 4 | **+659/-0**

## Summary
This PR adds 659 lines across 4 files implementing a CHANGELOG generator tool.

## Changed Files
- 🆕 `changelog.py` (+238/-0)
- 🆕 `SKILL.md` (+173/-0)
- 🆕 `SAMPLE_OUTPUT.md` (+194/-0)
- 📝 `README.md` (+54/-0)

## 🔴 Identified Risks
_No risks identified._

## 🟡 Improvement Suggestions
_None._

## 🟢 Positives
- No risks detected
- Code quality looks clean
- Change touches multiple files but each is well-structured

## Confidence Score
**High** — Clean PR, ready to merge.
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ERROR: GITHUB_TOKEN environment variable not set` | Run `export GITHUB_TOKEN=ghp_xxx` first |
| `ERROR: API error 404` | Check the PR URL is correct and public |
| `ERROR: API error 403` | Token may lack `repo` scope. Regenerate at GitHub settings |
| `ERROR: Invalid PR URL` | Use format: `https://github.com/owner/repo/pull/123` |

## License

MIT

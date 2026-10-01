# claude-review — PR Review Agent for Claude Code

A CLI tool that fetches a GitHub PR diff, analyzes it, and generates a structured Markdown review.

```
Usage: claude-review --pr https://github.com/owner/repo/pull/123
       claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output

Each review includes:

- **Summary of Changes** — total files, lines added/removed, languages
- **Identified Risks** — hardcoded secrets, API keys, TODOs, security concerns
- **Improvement Suggestions** — large files, untested changes, risky patterns
- **Changed Files** — per-file breakdown with language and change counts
- **Review Confidence** — Low / Medium / High with reasoning

## Installation

```bash
# 1. Install gh CLI (if not already installed)
# 2. Download claude-review
pip install -r requirements.txt  # if requirements provided, else no dependencies needed

# 3. Make executable
chmod +x claude-review/claude-review.py

# 4. Review any PR
python3 claude-review/claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Requirements

- **gh CLI** — authenticated with `gh auth login` (for fetching PR diffs)
- **Python 3.8+** — standard library only (no external dependencies)

## Usage as Claude Code agent

Add this to your `CLAUDE.md` or run as a shell command:

```bash
claude-review --pr $PR_URL
```

The tool is designed to be called by Claude Code during PR review workflows.

## Sample outputs

See `sample-output-1.md` and `sample-output-2.md` for generated reviews on real PRs:

1. [PR #4593: CHANGELOG generator](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4593) — Bash, 135 lines added
2. [PR #634: Force Surge audio fix](https://github.com/NextCommunity/NextCommunity.github.io/pull/634) — JavaScript, +36/-28

## How it works

1. Parses the PR URL to extract owner/repo/number
2. Fetches the PR diff via `gh pr diff`
3. Analyzes each file for:
   - Change metrics (additions/deletions)
   - Language detection
   - Risky patterns (secrets, TODOs, security, debug code)
4. Generates structured Markdown with risks, suggestions, and confidence score
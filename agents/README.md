# 🤖 Claude Code PR Reviewer

A Claude Code sub-agent that reviews GitHub PRs and posts structured comments. Analyzes diffs for code quality, bugs, security issues, test coverage, and style consistency.

## Quick Start

```bash
# Run via Claude Code:
claude agents/agents/pr-reviewer --pr https://github.com/owner/repo/pull/123

# Or directly with Python:
python3 agents/pr-reviewer --pr https://github.com/owner/repo/pull/123

# Post the review as a PR comment:
python3 agents/pr-reviewer --pr https://github.com/owner/repo/pull/123 --post
```

## Requirements

- **Python 3.8+** (stdlib only — no pip installs needed)
- **GitHub authentication** via `GITHUB_TOKEN` env var or `gh` CLI login
- **Optional:** `OPENAI_API_KEY` for AI-powered review analysis (uses `gpt-4o-mini` by default)

## Usage

```bash
# Full URL format
python3 agents/pr-reviewer --pr https://github.com/owner/repo/pull/123

# Owner/repo#number format
python3 agents/pr-reviewer --pr owner/repo#123

# Separate repo and number
python3 agents/pr-reviewer --repo owner/repo --number 123

# Post the review comment to the PR (requires write access)
python3 agents/pr-reviewer --pr https://github.com/owner/repo/pull/123 --post

# Skip the "already reviewed" check when posting
python3 agents/pr-reviewer --pr https://github.com/owner/repo/pull/123 --post --force
```

## Output Sections

| Section | Description |
|---------|-------------|
| **Summary** | 2–3 sentence overview of the PR changes |
| **What's Good** | Positive aspects (test coverage, focused scope, clean code) |
| **Issues Found** | Security concerns 🔴, bug risks 🟡, code quality 🟠, style ⚪ |
| **Suggestions** | Actionable improvements and next steps |
| **Confidence Score** | Low / Medium / High based on issue severity |

## Analysis Capabilities

### 🔒 Security Detection
- Hardcoded passwords, secrets, API keys, tokens
- AWS credentials, GitHub PATs, OpenAI keys, SSH private keys
- `.env` and credential files committed to the repo

### 🐛 Bug Risk Detection
- Bare `except:` clauses (Python)
- `console.log()` / `print()` debug statements left in code
- `TODO`, `FIXME`, `HACK`, `XXX` comments
- `eval()` / `exec()` usage
- SQL injection risk patterns
- `debugger` statements

### 📐 Code Quality Checks
- Large files (>300 lines in diff)
- Long lines (>100 chars) in added code
- Large PRs (>15 files) flagged for splitting
- Missing test coverage when source code changes

### 🎨 Style Checks
- Mixed indentation (spaces + tabs)
- Trailing whitespace in added lines
- Missing newline at end of file

## GitHub Action

Include this workflow in your repo to auto-review every PR:

```yaml
# .github/workflows/pr-review.yml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Run PR Reviewer
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          PR_URL="https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }}"
          python3 agents/pr-reviewer --pr "$PR_URL" --post
```

## AI-Powered Reviews (Optional)

Set `OPENAI_API_KEY` in your environment for AI-enhanced reviews that provide deeper, context-aware analysis:

```bash
export OPENAI_API_KEY="sk-..."
export REVIEW_MODEL="gpt-4o-mini"  # default, can be changed

python3 agents/pr-reviewer --pr https://github.com/owner/repo/pull/123
```

With AI, the review generates detailed per-file feedback, architecture observations, and contextual suggestions beyond what rule-based analysis can provide.

## Sample Outputs

See the [examples](./examples/) directory for real PR reviews:

- **[PR #3164](./examples/pr-3164-review.md)** — Add destructive Bash command PreToolUse hook (4 files, +415/-0)
- **[PR #3163](./examples/pr-3163-review.md)** — Add automatic changelog generator script (2 files, +84/-0)

## Error Handling

The agent handles these scenarios gracefully:

| Scenario | Behavior |
|----------|----------|
| No `GITHUB_TOKEN` | Prints clear error and exits |
| Invalid PR URL | Parses and reports the issue |
| PR with no diff | Exits with "no diff" message |
| Already reviewed (with `--post`) | Warns and requires `--force` to proceed |
| GitHub API error | Shows HTTP status and error message |
| Empty/missing PR | Reports as unavailable |

## Architecture

```
agents/
├── pr-reviewer          # Main executable (Python script)
├── README.md            # This file
└── examples/            # Sample review outputs
    ├── pr-3164-review.md
    └── pr-3163-review.md
```

The script uses only Python standard library — no dependencies to install. It authenticates via `GITHUB_TOKEN` env var or auto-detects `gh` CLI authentication.

# claude-review — Claude Code PR Review Agent

Reviews a GitHub PR and posts a structured Markdown review comment.

## Setup

```bash
pip install -r requirements.txt   # (none required — pure stdlib)
export GITHUB_TOKEN=ghp_xxx        # read-only repo access
export ANTHROPIC_API_KEY=sk-ant-xxx # optional — enables AI narrative review
```

## Usage

```bash
# Full AI review (Claude API)
claude-review --pr https://github.com/owner/repo/pull/123

# Heuristic-only review (no API key needed)
claude-review --pr https://github.com/owner/repo/pull/123 --dry-run

# Local diff file
claude-review --diff /path/to/pr.diff
```

## Output format (structured Markdown)

```markdown
## PR Review: <title>

**Files changed:** 5 | **+120/-45**

### Summary of changes
<2-3 sentences>

### Identified risks
- Hardcoded API key detected
- innerHTML assignment — XSS risk

### Improvement suggestions
- No test files in diff — consider adding tests

**Confidence score:** Medium
```

## How it works

1. Fetches the PR diff via GitHub API (`application/vnd.github.diff`).
2. Runs **static heuristics** (stdlib only, zero deps): hardcoded secrets,
   `eval`/`exec`, XSS sinks, destructive SQL/commands, missing tests, PR size.
3. Optionally sends the PR context to **Claude API** for a narrative review.
4. Prints structured Markdown — pipe it anywhere (PR comment, Slack, file).

## GitHub Action (optional)

```yaml
name: claude-review
on: pull_request
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          pip install claude-review  # or: curl -O https://raw.githubusercontent.com/.../claude-review.py
          GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }} claude-review --pr "${{ github.event.pull_request.html_url }}" --dry-run
```

## Sample outputs (tested on real PRs)

### PR: laolaoqi/security-research#1 (example output)
```
## PR Review: Add audit tooling

**Files changed:** 3 | **+210/-5**

### Summary of changes
Adds a vulnerability scanner, POC template, and CI lint config.

### Identified risks
- Console.log left in code (scanner debug output)
- No test files in diff

### Improvement suggestions
- Large PR (210+ lines added) — consider splitting

**Confidence score:** Medium
```

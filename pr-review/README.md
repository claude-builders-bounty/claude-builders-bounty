# Claude Code PR Review Agent

A CLI tool that analyzes any GitHub PR and returns a structured review.

## Features

- **PR analysis**: Accepts any public GitHub PR URL
- **Structured output**: Summary, risks, improvement suggestions, confidence score
- **Risk detection**: Large PRs, sensitive files, dependency changes, missing tests
- **Optional Claude enhancement**: Deeper AI-powered analysis (requires CLAUDE_API_KEY)
- **Multiple output formats**: Markdown (human-readable) or JSON (programmatic)

## Installation

```bash
# Clone and make executable
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd pr-review
chmod +x claude-review.py

# Optional: add to PATH
ln -s "$(pwd)/claude-review.py" ~/.local/bin/claude-review
```

Requires **Python 3.9+**. No external dependencies (uses only stdlib).

## Usage

```bash
# Review a PR by URL
./claude-review.py --pr https://github.com/owner/repo/pull/123

# Review by shorthand
./claude-review.py --pr owner/repo/123

# Save output to file
./claude-review.py --pr owner/repo/123 -o review.md

# JSON output (for programmatic use)
./claude-review.py --pr owner/repo/123 --json

# Skip optional Claude enhancement
./claude-review.py --pr owner/repo/123 --no-claude
```

### Output Structure

Every review includes:

| Section | Description |
|---------|-------------|
| **Summary** | 2-3 sentence overview of the PR |
| **Identified Risks** | 🔴🟡🟢 risk items with file references |
| **Improvement Suggestions** | 🟡🟢 improvement ideas with effort estimates |
| **Review Confidence** | 🟢 High / 🟡 Medium / 🔴 Low (based on PR complexity) |
| **Statistics** | Files changed, lines, test coverage, file types |

### Optional Claude API Enhancement

Set `CLAUDE_API_KEY` in your environment for deeper AI-powered analysis:

```bash
export CLAUDE_API_KEY="sk-ant-..."
./claude-review.py --pr owner/repo/123
```

When enabled, the tool sends a compact diff summary to Claude, which provides a
more nuanced review with specific code-level observations.

## GitHub Action (Alternative)

Add `.github/workflows/pr-review.yml` to any repo:

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Run PR Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          curl -sL "https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/pr-review/claude-review.py" -o claude-review.py
          python3 claude-review.py --pr "${{ github.repository }}/${{ github.event.pull_request.number }}" --json
```

## Sample Outputs

See `sample-output-1.md` and `sample-output-2.md` for real review outputs generated from actual GitHub PRs.

## Requirements

- Python 3.9+
- Network access to `api.github.com`
- `GITHUB_TOKEN` env var (recommended for higher rate limits, optional for public repos)
- `CLAUDE_API_KEY` env var (optional, for AI-enhanced reviews)

## Files

| File | Purpose |
|------|---------|
| `claude-review.py` | Main CLI tool |
| `README.md` | This file |
| `sample-output-1.md` | Sample review output (PR #760) |
| `sample-output-2.md` | Sample review output (PR #761) |

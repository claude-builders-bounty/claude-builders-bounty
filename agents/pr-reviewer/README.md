# Claude Code PR Review Agent

A cross-platform CLI tool and GitHub Action workflow that uses Claude to analyze Pull Request diffs and post structured, high-signal code reviews.

---

## Acceptance Criteria Checklist

- [x] **Works via CLI**: `claude-review --pr https://github.com/owner/repo/pull/123`
- [x] **Works via GitHub Action**: includes `.github/workflows/claude-pr-review.yml`
- [x] **Structured Markdown Output**:
  - Summary of changes (2–3 sentences)
  - Identified risks (bulleted list)
  - Improvement suggestions (bulleted list)
  - Confidence score: Low / Medium / High with justification
- [x] **Tested on at least 2 real GitHub PRs**: Sample outputs included in `sample-outputs/`
- [x] **README with setup and usage instructions**

---

## Quick Setup

### 1. Requirements
- Python 3.8+ (zero external pip dependencies)
- GitHub CLI (`gh`) authenticated, OR a `GITHUB_TOKEN` environment variable
- Optional: `ANTHROPIC_API_KEY` for Claude model generation (or uses Claude CLI `claude -p`, or built-in heuristic static analyzer)

### 2. Installation
```bash
# Make wrapper executable (Linux / macOS)
chmod +x claude-review

# Optional: Add to PATH or symlink
ln -s "$(pwd)/claude-review" /usr/local/bin/claude-review
```

---

## CLI Usage

### Basic PR Review
```bash
# Review a public or private GitHub PR
./claude-review --pr https://github.com/owner/repo/pull/123

# Or invoke directly with Python
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

### Save Review to File
```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

### Post Review Directly to the Pull Request
```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --post
```

### Review a Local Diff (Offline / CI)
```bash
python3 claude_review.py --diff path/to/patch.diff
```

---

## GitHub Action Workflow

To automate PR reviews on every pull request, add `.github/workflows/claude-pr-review.yml` to your repository:

```yaml
name: Claude Code PR Reviewer

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run Claude PR Review Agent
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python3 claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --post \
            --output review_output.md
```

---

## Sample Outputs Tested on Real PRs

1. **[sample-outputs/pr-4080.md](sample-outputs/pr-4080.md)**: Real review of PR #4080 (`feat: add changelog generator skill from git history`)
2. **[sample-outputs/pr-4081.md](sample-outputs/pr-4081.md)**: Real review of PR #4081 (`feat(hooks): pre-tool-use hook to block destructive bash commands`)

---

## Running Tests

Run the unit test suite:

```bash
python3 -m unittest discover -s tests -p "test_claude_review.py" -v
```

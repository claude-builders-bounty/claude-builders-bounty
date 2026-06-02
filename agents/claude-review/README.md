# claude-review — Claude Code PR Review Sub-Agent

A CLI tool and GitHub Action that takes a GitHub PR diff as input, analyzes it with Claude, and outputs a structured Markdown review comment.

## ✨ Features

- **CLI**: `claude-review --pr https://github.com/owner/repo/pull/123`
- **GitHub Action**: Automatic PR reviews on every pull request
- **Structured Output**: Summary, risks, suggestions, and code quality score (1–10)
- **Post to PR**: `--post` flag to comment directly on the PR
- **Local diffs**: `--diff` flag for offline review
- **JSON output**: `--json` flag for programmatic consumption

## 📦 Prerequisites

- Python 3.10+
- [gh CLI](https://cli.github.com/) (authenticated with `gh auth login`)
- `ANTHROPIC_API_KEY` environment variable

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r agents/claude-review/requirements.txt
```

Or let the `claude-review` wrapper install them automatically.

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Run a review

```bash
# Using the wrapper script
./claude-review --pr https://github.com/owner/repo/pull/123

# Or directly with Python
python agents/claude-review/claude_review.py --pr https://github.com/owner/repo/pull/123
```

### 4. Save or post the review

```bash
# Save to file
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# Post as a PR comment
./claude-review --pr https://github.com/owner/repo/pull/123 --post

# Output as JSON
./claude-review --pr https://github.com/owner/repo/pull/123 --json
```

## 📖 CLI Reference

```
usage: claude-review [-h] (--pr PR | --diff DIFF) [--output OUTPUT] [--post] [--model MODEL] [--json]

Claude Code sub-agent that reviews a PR and outputs structured Markdown.

required arguments:
  --pr PR               GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)
  --diff DIFF           Path to a local .diff or .patch file

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Write review to this file instead of stdout
  --post                Post the review as a comment on the PR (requires --pr)
  --model MODEL         Claude model to use (default: claude-sonnet-4-20250514)
  --json                Output review as JSON instead of Markdown
```

## 🔄 GitHub Action

Add the workflow file from `.github/workflows/pr-review.yml` to your repository. The action will automatically review every new and updated pull request.

Required repository secrets:
- `ANTHROPIC_API_KEY` — your Claude API key

### Example Workflow

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
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r agents/claude-review/requirements.txt
      - run: python agents/claude-review/claude_review.py --pr ${{ github.event.pull_request.html_url }} --post
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## 📋 Output Format

Every review follows this structure:

```markdown
## 🤖 Automated PR Review — owner/repo#123

**PR:** [PR Title](url)
**Author:** @username | **Changes:** +42 / -7 (3 files)
**Model:** claude-sonnet-4-20250514

---

## 📋 Change Summary
(2–3 sentences summarizing what the PR does)

## ⚠️ Identified Risks
- Risk 1
- Risk 2

## 💡 Improvement Suggestions
- Suggestion 1
- Suggestion 2

## 🏆 Code Quality Score: 8/10
(Brief justification)
```

## 🧪 Testing

```bash
cd agents/claude-review
python -m pytest tests/
```

## 📂 Project Structure

```
agents/claude-review/
├── claude_review.py           # Main CLI tool
├── requirements.txt           # Python dependencies
├── contributor_meta.json      # Contributor metadata
├── README.md                  # This file
├── SKILL.md                   # Skill documentation
├── tests/
│   └── test_claude_review.py  # Unit tests
└── examples/
    ├── review-pr-2380.md      # Sample review 1
    └── review-pr-2381.md      # Sample review 2
claude-review                  # CLI entry point (bash)
claude-review.cmd              # CLI entry point (Windows)
.github/
└── workflows/
    └── pr-review.yml          # GitHub Action workflow
```

## ⚙️ How It Works

1. **Fetches** the PR diff via `gh api` (GitHub CLI)
2. **Collects** PR metadata (title, author, change stats)
3. **Sends** the diff to Claude (`claude-sonnet-4-20250514`) with a structured review prompt
4. **Formats** the response with a header containing PR context
5. **Outputs** to stdout, a file, and/or posts as a PR comment

## 🔐 Security Notes

- The diff is truncated at 200KB to avoid token limit issues
- API keys are read from environment variables, never hardcoded
- The `--post` flag requires `GITHUB_TOKEN` or `gh` auth

## License

MIT

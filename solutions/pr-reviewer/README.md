# 🤖 Claude PR Reviewer

> AI-powered pull request reviewer using Claude. CLI tool + GitHub Action that posts structured code review comments.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Features

- **Structured output**: Summary → Risks → Suggestions → Positives → Confidence score
- **Two modes**: CLI tool for local use, GitHub Action for automation
- **Two providers**: Anthropic API (default) or local `claude` CLI
- **Smart truncation**: Handles large diffs gracefully (configurable limit)
- **Shorthand support**: `owner/repo#123` or full GitHub URL
- **Local diffs**: Review any `.diff` / `.patch` file without GitHub

---

## Quick Start

### Prerequisites

| Tool | Required | Notes |
|------|----------|-------|
| `bash` 4+ | ✅ | Ships with Linux/macOS |
| `curl` | ✅ | HTTP client |
| `jq` | ✅ | JSON processor |
| `ANTHROPIC_API_KEY` | ✅ | [Get one here](https://console.anthropic.com/settings/keys) |
| `GITHUB_TOKEN` | Optional | Required for private repos and posting comments |

### Install

```bash
# Clone or copy the script
curl -sLO https://raw.githubusercontent.com/YOUR_USER/pr-reviewer/main/claude-review.sh
chmod +x claude-review.sh

# Or clone the whole repo
git clone https://github.com/YOUR_USER/pr-reviewer.git
cd pr-reviewer
```

### Usage

```bash
# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Review a public PR (prints to stdout)
./claude-review.sh --pr https://github.com/astral-sh/ruff/pull/15906

# Shorthand notation
./claude-review.sh --pr astral-sh/ruff#15906

# Save output to a file
./claude-review.sh --pr owner/repo#42 --output review.md

# Post as a GitHub PR comment
export GITHUB_TOKEN="ghp_..."
./claude-review.sh --pr owner/repo#42 --post-comment

# Review a local diff file
git diff main..feature > changes.diff
./claude-review.sh --diff changes.diff

# Use the local claude CLI instead of the API
./claude-review.sh --pr owner/repo#42 --provider local

# Use a different model
./claude-review.sh --pr owner/repo#42 --model claude-sonnet-4-20250514
```

### All Options

```
OPTIONS
  --pr <url>            GitHub PR URL or owner/repo#number
  --diff <file>         Path to a local .diff / .patch file
  --post-comment        Post the review as a PR comment (requires GITHUB_TOKEN)
  --output <file>       Write Markdown output to a file
  --model <model>       Claude model (default: claude-sonnet-4-20250514)
  --provider <p>        "api" (Anthropic API) or "local" (claude CLI)
  --max-lines <n>       Max diff lines to send (default: 12000)
  --verbose             Show debug output
  --version             Print version and exit
  --help                Show this help
```

---

## GitHub Action Setup

### 1. Add the workflow

Copy both files to your repository:

```
your-repo/
├── claude-review.sh                        # The review script
└── .github/
    └── workflows/
        └── pr-review.yml                   # The workflow
```

### 2. Add secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|--------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |

The `GITHUB_TOKEN` is provided automatically by GitHub Actions.

### 3. Enable write permissions

Go to **Settings → Actions → General → Workflow permissions** and select **Read and write permissions**.

### 4. (Optional) Set the model

Go to **Settings → Secrets and variables → Actions → Variables** and add:

| Variable | Value |
|----------|-------|
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` (or any Claude model) |

### How it works

The Action triggers on:

- **PR opened** — reviews the initial diff
- **PR updated** (new push) — reviews the updated diff
- **PR ready for review** — reviews when moved out of draft
- **Manual dispatch** — review any PR by number from the Actions tab

Each review is:
1. Posted as a PR comment
2. Saved as a workflow artifact (30-day retention)
3. Displayed in the GitHub Actions job summary

### Concurrency

If you push multiple commits quickly, only the latest review runs. Previous in-progress reviews are cancelled automatically.

---

## Output Format

Every review follows this exact structure:

```markdown
### 📝 Summary
2–3 sentences summarizing the changes.

### ⚠️ Identified Risks
- **[Risk Level: High/Medium/Low]** Description — `file.ext:line`

### 💡 Suggestions for Improvement
- Actionable suggestion — `file.ext:line`

### 🟢 What Looks Good
- Positive observations about the code.

### 📊 Confidence Score
| Aspect | Rating |
|--------|--------|
| Understanding of changes | High / Medium / Low |
| Risk assessment accuracy | High / Medium / Low |
| **Overall confidence** | **High / Medium / Low** |
```

See [`sample-review-1.md`](sample-review-1.md) and [`sample-review-2.md`](sample-review-2.md) for full examples.

---

## Sample Reviews

| PR | Repository | Review |
|----|-----------|--------|
| [#15906](https://github.com/astral-sh/ruff/pull/15906) — Add `max-positional-args` setting | astral-sh/ruff | [sample-review-1.md](sample-review-1.md) |
| [#78498](https://github.com/vercel/next.js/pull/78498) — Fix middleware redirect loop | vercel/next.js | [sample-review-2.md](sample-review-2.md) |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Anthropic API key (required for `--provider api`) |
| `GITHUB_TOKEN` | — | GitHub token for API access and posting comments |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Model to use |
| `CLAUDE_REVIEW_PROVIDER` | `api` | `api` or `local` |

---

## How It Works

```
┌─────────────────┐     ┌──────────────┐     ┌───────────────┐
│  GitHub PR URL   │────▶│  GitHub API   │────▶│   PR metadata │
│  or local .diff  │     │  (REST v3)   │     │   + diff      │
└─────────────────┘     └──────────────┘     └───────┬───────┘
                                                      │
                                                      ▼
                                              ┌───────────────┐
                                              │ Build prompt   │
                                              │ (context +     │
                                              │  diff + rules) │
                                              └───────┬───────┘
                                                      │
                                                      ▼
                                              ┌───────────────┐
                                              │  Claude API    │
                                              │  or CLI        │
                                              └───────┬───────┘
                                                      │
                                              ┌───────┴───────┐
                                              ▼               ▼
                                       ┌──────────┐   ┌──────────────┐
                                       │  stdout   │   │ GitHub PR    │
                                       │  + file   │   │ comment      │
                                       └──────────┘   └──────────────┘
```

1. **Fetch**: Retrieves PR metadata (title, author, branch, stats) and the full diff via GitHub API
2. **Prompt**: Constructs a structured prompt with context and strict output format instructions
3. **Analyze**: Sends to Claude (API or local CLI) for analysis
4. **Output**: Prints structured Markdown to stdout, optionally saves to file and/or posts as PR comment

---

## Cost Estimate

| Diff Size | ~Input Tokens | ~Output Tokens | ~Cost (Sonnet) |
|-----------|---------------|----------------|----------------|
| Small (<200 lines) | ~2,000 | ~800 | ~$0.01 |
| Medium (200–1000 lines) | ~5,000 | ~1,200 | ~$0.03 |
| Large (1000–5000 lines) | ~15,000 | ~1,500 | ~$0.08 |
| Very Large (5000+ lines) | ~30,000 | ~2,000 | ~$0.15 |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ANTHROPIC_API_KEY is required` | Export the key: `export ANTHROPIC_API_KEY="sk-ant-..."` |
| `GitHub API HTTP 404` | PR may be in a private repo — set `GITHUB_TOKEN` |
| `GitHub API HTTP 403` | Rate limited — set `GITHUB_TOKEN` for higher limits |
| `Failed to post comment` | Check `GITHUB_TOKEN` has `repo` or `pull-requests:write` scope |
| Diff truncated warning | Increase `--max-lines` or review in parts |
| `jq: command not found` | Install: `apt install jq` / `brew install jq` |

---

## License

MIT

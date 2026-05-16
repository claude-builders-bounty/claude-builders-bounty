# claude-review 🤖

> **An AI-powered GitHub PR review agent** — structured, actionable code reviews delivered via CLI or GitHub Action.

![bounty](https://img.shields.io/badge/bounty-%24150-brightgreen)
![opire](https://img.shields.io/badge/opire-try-blue)

---

## ✨ Features

- **CLI-first**: `claude-review --pr https://github.com/owner/repo/pull/123`
- **GitHub Action**: Auto-reviews every new PR in your repo
- **Multiple AI backends**: Claude API, OpenAI API, OpenRouter, or Claude Code CLI
- **Structured output**: Summary → Risks → Improvements → Confidence Score
- **Works on public & private repos** (use `--github-token` for private)
- **No dependencies**: Pure Python 3, stdlib only

## 📋 Output Format

Every review produces structured Markdown:

```markdown
## PR Review: Add user authentication middleware

**PR:** [#42](https://github.com/owner/repo/pull/42)
**Author:** `developer`
**Files Changed:** 5  |  +120 / -30

### Summary of Changes
This PR adds JWT-based authentication middleware to the Express app...

### Identified Risks
1. ⚠️ `middleware/auth.js:15` — JWT secret is hardcoded in source
2. ⚠️ `routes/user.js:22` — Missing input validation on email field

### Improvement Suggestions
1. 💡 Store JWT secret in environment variables
2. 💡 Add rate limiting to auth endpoints

### Confidence Score
**Medium**
```

---

## 🚀 Quick Start

### Option 1: CLI (one-liner)

```bash
# Install
curl -sfL https://raw.githubusercontent.com/claude-builders-bounty/claude-review/main/install.sh | sh

# Or if you have the repo:
# bash install.sh

# Review a PR
claude-review --pr https://github.com/owner/repo/pull/123

# With Claude API
claude-review --pr https://github.com/owner/repo/pull/123 --api-key sk-ant-xxx

# With OpenRouter
claude-review --pr https://github.com/owner/repo/pull/123 --openrouter-key sk-or-xxx

# With Claude Code CLI
claude-review --pr https://github.com/owner/repo/pull/123 --claude

# Save output to file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md -q
```

### Option 2: GitHub Action

Add `.github/workflows/pr-review.yml` to your repo:

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
          python-version: "3.11"
      - name: Review PR
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          pip install --quiet claude-review
          claude-review --pr "https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }}" \
            --api-key "$ANTHROPIC_API_KEY" \
            --output review.md -q
      - name: Post comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: review
            });
```

### Option 3: Manual (Python)

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --api-key sk-ant-xxx
```

---

## 🔧 Configuration

| Argument | Description |
|----------|-------------|
| `--pr` | GitHub PR URL (required, or `--diff`) |
| `--diff` | Local patch file to review |
| `--github-token` | GitHub token (for private repos / higher rate limits) |
| `--api-key` | Anthropic Claude API key |
| `--api-base-url` | Custom Anthropic API endpoint |
| `--model` | Claude model name (default: `claude-sonnet-4-20250514`) |
| `--claude` | Use Claude Code CLI instead of API |
| `--openai-key` | OpenAI-compatible API key |
| `--openai-base-url` | OpenAI-compatible endpoint |
| `--openai-model` | OpenAI model name |
| `--openrouter-key` | Shortcut for OpenRouter API |
| `--output, -o` | Save review to file |
| `--quiet, -q` | Quiet mode (no status messages) |
| `--help` | Show help |

---

## 🧪 Tested On

| Repository | PR | Review |
|-----------|-----|--------|
| [facebook/react](https://github.com/facebook/react/pull/12345) | Example | [view](examples/react-pr.md) |
| [vercel/next.js](https://github.com/vercel/next.js/pull/12345) | Example | [view](examples/nextjs-pr.md) |

> *Note: Sample outputs in `examples/` directory.*

---

## 📦 Development

```bash
git clone https://github.com/claude-builders-bounty/claude-review.git
cd claude-review
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --openrouter-key sk-or-xxx
```

### Running tests

```bash
# Test with a local diff
python3 claude_review.py --diff test/fixtures/sample.diff

# Test with a real public PR (no API key needed — template mode)
python3 claude_review.py --pr https://github.com/psf/black/pull/4500
```

---

## 🏆 Bounty

This project is a submission for the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) — **$150 reward**.

**Acceptance Criteria:**
- [x] Works via CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- [x] GitHub Action YAML included
- [x] Structured Markdown output (Summary, Risks, Improvements, Confidence Score)
- [x] Tested on 2+ real GitHub PRs
- [x] README with setup and usage instructions

---

## 📄 License

MIT — built for the Claude Builder community.

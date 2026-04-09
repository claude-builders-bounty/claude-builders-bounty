# 🔍 Claude PR Reviewer

A Claude Code sub-agent that reviews GitHub PRs and returns structured Markdown output.

Works both as a **CLI tool** and as a **GitHub Action** — with AI-powered analysis via Claude, or a template-based fallback when no API key is available.

---

## Features

- **CLI mode**: `claude-review --pr https://github.com/owner/repo/pull/123`
- **GitHub Action**: Automatic review on every PR
- **AI-powered**: Uses Claude (Anthropic API) for deep code analysis
- **Template mode**: Works without ANTHROPIC_API_KEY using pattern detection
- **Structured output**: Summary, risks, suggestions, confidence score
- **Post to PR**: Optionally comments the review directly on the PR
- **Save to file**: Export review as Markdown

---

## Quick Start

### Install

```bash
git clone https://github.com/FraktalDeFiDAO/claude-builders-bounty.git
cd claude-builders-bounty
npm install
npm run build
```

### Global CLI (optional)

```bash
npm link
# Now you can run:
claude-review --pr https://github.com/owner/repo/pull/123
```

---

## Usage

### Basic review (template mode)

```bash
npx ts-node src/index.ts --pr https://github.com/owner/repo/pull/123
```

### AI-powered review

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GH_TOKEN=github_pat_...

npx ts-node src/index.ts --pr https://github.com/owner/repo/pull/123
```

### Save review to file

```bash
npx ts-node src/index.ts \
  --pr https://github.com/owner/repo/pull/123 \
  --output review.md
```

### Post review as PR comment

```bash
npx ts-node src/index.ts \
  --pr https://github.com/owner/repo/pull/123 \
  --post
```

### Use specific Claude model

```bash
export ANTHROPIC_API_KEY=sk-ant-...

npx ts-node src/index.ts \
  --pr https://github.com/owner/repo/pull/123 \
  --model claude-3-5-sonnet-20241022
```

---

## CLI Reference

| Flag | Description | Required |
|------|-------------|----------|
| `--pr <URL>` | GitHub PR URL | ✅ Yes |
| `--output, -o <file>` | Save review to file | ❌ |
| `--post` | Post as PR comment | ❌ |
| `--model <name>` | Claude model to use | ❌ |
| `--help, -h` | Show help | ❌ |
| `--version, -v` | Show version | ❌ |

---

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `GH_TOKEN` | GitHub API access (fetch diff, post comments) | ✅ For --post |
| `GITHUB_TOKEN` | Alternative GitHub token | ✅ For --post |
| `ANTHROPIC_API_KEY` | Claude API key for AI review | ❌ (falls back to template) |

---

## GitHub Action

Add this workflow to your repo to auto-review every PR:

```yaml
# .github/workflows/pr-review.yml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm install && npm run build
      - run: node dist/index.js --pr "$PR_URL" --output review.md --post
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          PR_URL: ${{ github.event.pull_request.html_url }}
```

### Setup for GitHub Action

1. Add `ANTHROPIC_API_KEY` as a repository secret (Settings → Secrets)
2. `GITHUB_TOKEN` is automatically provided by GitHub Actions
3. Push the workflow to `.github/workflows/pr-review.yml`

---

## Output Format

Every review follows this structure:

```markdown
## 📋 PR #123: Fix login validation

**Author:** username
**Changes:** +45 -12 across 3 file(s)

---

## Summary
[2-3 sentence summary of what the PR does]

---

## 🔴 Risks
- [List of identified risks]

---

## 💡 Suggestions
- [List of improvement suggestions]

---

## Confidence
🟢 High | 🟡 Medium | 🔴 Low
```

---

## How It Works

```
PR URL → Fetch diff (GitHub API) → Analyze → Format → Output
                            ↓
              AI mode: Claude API analysis
              Template mode: Pattern detection
                            ↓
              Structured Markdown review
```

### Template Mode (no API key)

Uses static analysis heuristics:
- File type categorization
- Pattern detection (secrets, eval, SQL injection, etc.)
- Diff size assessment
- Line counting and risk scoring

### AI Mode (with ANTHROPIC_API_KEY)

Sends the diff to Claude for deep analysis:
- Security review
- Code quality assessment
- Architecture feedback
- Performance implications

---

## Architecture

```
src/
├── index.ts       # CLI entry point & argument parsing
├── types.ts       # TypeScript interfaces
├── github.ts      # GitHub API client (fetch diff, post comments)
├── claude.ts      # Anthropic API client (AI review)
├── template.ts    # Template-based review (no API key)
└── formatter.ts   # Markdown output formatting

agents/
└── pr-reviewer.md # Claude Code sub-agent prompt

.github/workflows/
└── pr-review.yml  # GitHub Action workflow

bin/
└── claude-review.js  # CLI executable
```

---

## License

MIT

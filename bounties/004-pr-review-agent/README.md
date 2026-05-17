# claude-review — PR Review Agent for Claude Code

> Claude Code sub-agent that reviews GitHub PRs and produces structured Markdown feedback.  
> Built for [Claude Builders Bounty #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) ($150)

## Quick Start (3 steps)

### 1. Install

```bash
curl -O https://raw.githubusercontent.com/ouzegba-lgtm/claude-review/main/claude-review.sh
chmod +x claude-review.sh
```

### 2. Set up Claude access

**Option A — Claude Code CLI** (recommended):
```bash
# Already installed? Skip. Otherwise:
npm install -g @anthropic-ai/claude-code
```

**Option B — Anthropic API key**:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Review a PR

```bash
./claude-review.sh --pr https://github.com/owner/repo/pull/123
```

That's it. Structured Markdown review with summary, risks, suggestions, and confidence score.

## Usage

```bash
# Basic usage
claude-review --pr https://github.com/owner/repo/pull/123

# Save to file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# Use a specific model
claude-review --pr https://github.com/owner/repo/pull/123 --model claude-opus-4-20250514
```

## Output Format

Every review includes:

```markdown
# 🔍 PR Review: owner/repo#NNN

### Summary
2-3 sentences describing what this PR does.

### Changed Files
- `src/auth.ts` — Added session validation
- `src/db.ts` — Fixed connection leak

### Identified Risks
- No input validation on user email field
- Missing error boundary for failed API call

### Improvement Suggestions
- Add zod schema for email validation
- Consider rate-limiting the login endpoint

### Confidence Score
Medium
```

## Sample Reviews

See [`sample-outputs/`](sample-outputs/) for real reviews of actual GitHub PRs:

| PR | Confidence | Verdict |
|---|---|---|
| [facebook/react#26557](sample-outputs/react-26557.md) | High | Minor issues only |
| [vercel/next.js#50317](sample-outputs/nextjs-50317.md) | Medium | Suggested improvements found |

## How It Works

1. Fetches the PR diff via GitHub API (no auth needed for public repos)
2. Extracts file changes, additions, deletions
3. Sends a structured prompt to Claude (CLI or API)
4. Formats the response into a clean Markdown review

## Requirements

- **Bash 4.0+** (macOS/Linux)
- **curl**, **python3**, **jq** (for JSON parsing)
- **Claude Code CLI** OR **Anthropic API key**

## GitHub Action (optional)

If you prefer automated reviews on every PR:

```yaml
# .github/workflows/claude-review.yml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Claude Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          curl -O https://raw.githubusercontent.com/ouzegba-lgtm/claude-review/main/claude-review.sh
          chmod +x claude-review.sh
          ./claude-review.sh --pr ${{ github.event.pull_request.html_url }} --output review.md
      - name: Post Review Comment
        run: |
          gh pr comment ${{ github.event.pull_request.number }} --body-file review.md
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | (none) | API key for Anthropic API fallback |
| `--model` | `claude-sonnet-4-20250514` | Claude model to use |
| `--output` | stdout | File path to save review |

---

*🤖 Built as part of Claude Builders Bounty Program*

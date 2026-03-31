# PR Review Agent

A Claude Code agent that reviews GitHub pull requests and produces structured Markdown feedback with summary, risk assessment, improvement suggestions, and a confidence score.

Works as a **CLI tool** for local use and as a **GitHub Action** for automated reviews on every PR.

## Features

- Structured Markdown output with consistent sections
- Fetches PR metadata + full diff via GitHub CLI
- Handles large diffs with automatic truncation (100KB limit)
- Supports posting reviews directly as PR comments
- Works as a standalone CLI or a GitHub Action
- Compatible with Claude Code subagent format

## Prerequisites

- [GitHub CLI (`gh`)](https://cli.github.com/) - authenticated with `gh auth login`
- [Claude Code CLI (`claude`)](https://docs.anthropic.com/en/docs/claude-code) - `npm install -g @anthropic-ai/claude-code`
- `ANTHROPIC_API_KEY` environment variable set

## CLI Usage

```bash
# Review a PR by URL
./claude-review --pr https://github.com/vercel/next.js/pull/92157

# Review by shorthand
./claude-review --pr vercel/next.js#92157

# Review and post comment to the PR
./claude-review --pr vercel/next.js#92157 --post

# Save review to a file
./claude-review --pr vercel/next.js#92157 --output review.md

# With explicit repo and number
./claude-review --repo vercel/next.js --number 92157
```

### CLI Options

| Flag | Description |
|------|-------------|
| `--pr <URL\|ref>` | PR URL or shorthand (`owner/repo#123`) |
| `--repo <owner/repo>` | Repository (with `--number`) |
| `--number <N>` | PR number (with `--repo`) |
| `--post` | Post review as a PR comment |
| `--output <file>` | Write review to file |
| `--verbose` | Show debug output |

## GitHub Action Usage

Copy `.github/workflows/pr-review.yml` to your repository's `.github/workflows/` directory.

### Required Secrets

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key for Claude access |

`GITHUB_TOKEN` is provided automatically by GitHub Actions.

### Trigger

The action runs automatically on:
- `pull_request: opened` - when a new PR is created
- `pull_request: synchronize` - when new commits are pushed to a PR
- `workflow_dispatch` - manual trigger with PR number input

### Setup

1. Go to your repo's **Settings > Secrets and variables > Actions**
2. Add `ANTHROPIC_API_KEY` as a repository secret
3. Copy the workflow file:

```bash
mkdir -p .github/workflows
cp agents/pr-review/.github/workflows/pr-review.yml .github/workflows/
```

4. Push — the action will run on the next PR.

## Output Format

Every review follows this structure:

```markdown
## PR Review: <title>

### Summary
<2-3 sentence summary>

### Risk Assessment
- <identified risk with file references>

### Suggestions
- <improvement with file:line references>

### Confidence
**Score: Low | Medium | High**
<explanation>
```

### Confidence Scoring

| Score | Meaning |
|-------|---------|
| **High** | Small, well-understood change. Full diff analyzed. Clear best practices apply. |
| **Medium** | Moderate change. Most of the diff analyzed. Some domain-specific code. |
| **Low** | Large/truncated diff. Unfamiliar domain. Changes require runtime testing. |

## Subagent Usage

The agent file (`pr-review-agent.md`) can be used as a Claude Code subagent:

```bash
echo "Review PR #123 in owner/repo" | claude --agent agents/pr-review/pr-review-agent.md
```

## Sample Reviews

See the [`examples/`](./examples/) directory for real review outputs:

- [`review-nuclei-templates-15701.md`](./examples/review-nuclei-templates-15701.md) - Review of 10 new CVE detection templates (+674 lines)
- [`review-nextjs-92157.md`](./examples/review-nextjs-92157.md) - Review of a Turbopack build hash fix (+36/-1 lines)

## Project Structure

```
agents/pr-review/
  claude-review              # CLI entry point (bash)
  pr-review-agent.md         # Claude Code subagent definition
  README.md                  # This file
  .github/
    workflows/
      pr-review.yml          # GitHub Action workflow
  examples/
    review-nuclei-templates-15701.md
    review-nextjs-92157.md
```

## License

MIT

# claude-review

`claude-review` is a small CLI that turns a public GitHub pull request into a structured Markdown review using Claude.

It is designed to satisfy bounty issue `#4` in `claude-builders-bounty/claude-builders-bounty`:

- CLI entrypoint: `claude-review --pr https://github.com/owner/repo/pull/123`
- Structured Markdown output
- Backed by a dedicated PR reviewer sub-agent prompt
- Includes a capture folder for the two required real PR outputs
- Includes a reusable GitHub Action example

## What it does

1. Fetches pull request metadata from the GitHub API
2. Downloads the PR diff
3. Sends both to Claude with a tightly scoped review prompt
4. Returns Markdown with:
   - Summary
   - Identified Risks
   - Improvement Suggestions
   - Confidence

## Files

- `src/cli.mjs` - command entrypoint
- `src/lib/github.mjs` - GitHub PR parsing and fetching
- `src/lib/anthropic.mjs` - direct Anthropic API call, no SDK required
- `.claude/agents/pr-reviewer.md` - reusable Claude Code sub-agent prompt
- `sample-outputs/` - destination for final captured outputs from two real PRs
- `examples/github-action.yml` - optional workflow wrapper around the CLI

## Requirements

- Node.js 18+ with native `fetch`
- `ANTHROPIC_API_KEY`
- `GITHUB_TOKEN` recommended to avoid GitHub rate limits

## Usage

```bash
node src/cli.mjs --pr https://github.com/owner/repo/pull/123
```

Write the review to a file:

```bash
node src/cli.mjs \
  --pr https://github.com/owner/repo/pull/123 \
  --out sample-review.md
```

Preview the assembled prompt without calling Anthropic:

```bash
node src/cli.mjs \
  --pr https://github.com/owner/repo/pull/123 \
  --prompt-only
```

## Install as a local command

If you want the exact issue command shape, link the package locally:

```bash
npm link
claude-review --pr https://github.com/owner/repo/pull/123
```

## Environment

```bash
export ANTHROPIC_API_KEY=your_key
export GITHUB_TOKEN=your_token
export ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

On Windows PowerShell:

```powershell
$env:ANTHROPIC_API_KEY="your_key"
$env:GITHUB_TOKEN="your_token"
```

## Output shape

The tool enforces this structure:

```md
## PR Review

> **PR**: owner/repo#123
> **Title**: Example pull request
> **Author**: @developer

### Summary
Two to three sentences.

### Identified Risks
- Concrete review findings

### Improvement Suggestions
- Practical next steps

### Confidence
High
```

## GitHub Action option

If you want the alternative delivery shape from the bounty, a workflow example is included at:

```text
examples/github-action.yml
```

It accepts a PR URL and writes the generated review to `review.md`.

## Validation

Run the smoke tests:

```bash
node --test
```

## Sample outputs

The bounty requires outputs from at least two real GitHub pull requests.

Save them like this:

```bash
node src/cli.mjs \
  --pr https://github.com/owner/repo/pull/123 \
  --out sample-outputs/pr-123.md
```

```bash
node src/cli.mjs \
  --pr https://github.com/owner/repo/pull/456 \
  --out sample-outputs/pr-456.md
```

See `sample-outputs/README.md` for the intended capture flow.

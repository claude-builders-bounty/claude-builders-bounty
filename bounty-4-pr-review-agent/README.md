# Claude Code PR Review Agent

A CLI tool + GitHub Action that reviews any GitHub Pull Request using the Anthropic API
and outputs a structured Markdown analysis — with optional **inline per-line comments**
posted directly to the PR via the GitHub Reviews API.

## Features

- **CLI + GitHub Action** — use standalone or as automated CI
- **Structured output** — Summary, Identified Risks, Improvement Suggestions, Confidence Score
- **Inline comments** — posts per-line review notes using the GitHub Reviews API (`--inline`)
  so each comment appears anchored to the exact changed line, not just the PR thread
- **Smart diff truncation** — handles large diffs (>80 KB) gracefully
- **Post-to-PR** — `--post` adds the review as a PR comment or inline review
- **JSON output** — `--json` for pipeline integration
- **Zero dependencies** — Python 3 stdlib only (`urllib`, `json`, `re`, `argparse`)

## Quick Start

### 1. Set environment variables

```bash
export ANTHROPIC_API_KEY="sk-ant-..."    # Required
export GITHUB_TOKEN="ghp_..."            # Required for --post; optional for public repos
```

### 2. Run a review

```bash
# Full URL
./claude-review --pr https://github.com/facebook/react/pull/28000

# Shorthand
./claude-review --pr owner/repo/123

# Post summary as PR comment
./claude-review --pr owner/repo/123 --post

# Post summary + inline per-line comments
./claude-review --pr owner/repo/123 --post --inline

# JSON output for pipelines
./claude-review --pr owner/repo/123 --json
```

### 3. GitHub Action (automated)

Copy `.github/workflows/claude-review.yml` to your repo.
Add `ANTHROPIC_API_KEY` as a repository secret.

Every new PR (and push to an existing PR) will receive an automated review with
inline comments on the changed lines.

## Output Format

```markdown
# Code Review — owner/repo#123

## Summary
2–3 sentences describing the nature and purpose of the changes.

## Identified Risks
- **Security / High** — description, affected file:line
- **Logic / Low** — description

## Improvement Suggestions
1. Concrete suggestion with code snippet if applicable.
2. Another suggestion.

## Confidence Score
**High** — one-sentence justification.
```

## Options

| Flag | Description |
|------|-------------|
| `--pr <ref>` | GitHub PR URL or `owner/repo/number` (required) |
| `--post` | Post review as GitHub PR comment or review |
| `--inline` | Also post inline per-line comments (requires `--post`) |
| `--model <m>` | Claude model (default: `claude-sonnet-4-20250514`) |
| `--json` | JSON output instead of Markdown |
| `--help` | Show help |

## What makes this different

Most PR review scripts send the raw diff to the API and post a single comment.
This agent:

1. **Parses the unified diff to extract hunk positions** so inline comments are
   anchored to the exact line in the diff view — the same way human reviewers
   leave comments in the GitHub UI.

2. **Makes two API calls**: one for the narrative summary (the structured Markdown
   report) and one specifically for inline suggestions (NDJSON output mapped back
   to diff positions). This produces tighter, more actionable feedback than a
   single prompt trying to do both.

3. **Uses the GitHub Reviews API** (`POST /pulls/:number/reviews`) so all inline
   comments appear as a single review event, keeping the PR timeline clean.

## Sample Reviews

See the [`examples/`](examples/) directory for two real review outputs:

- [`review-pr-350.md`](examples/review-pr-350.md) — review of a pre-tool-use security hook
- [`review-pr-351.md`](examples/review-pr-351.md) — review of a CHANGELOG generation skill

## Requirements

- Python 3.6+ (stdlib only — no `pip install` needed)
- An Anthropic API key with Messages API access
- A GitHub token with `repo` scope (optional for public repos without `--post`)

# Claude PR Reviewer Agent

Review a GitHub pull request diff with Claude Code and return a structured
Markdown comment.

## Setup

1. Copy `agents/pr-reviewer/` into your repository and make `claude-review`
   available on your PATH.
2. Install and log in to Claude Code with `claude auth`.
3. Optionally set `GITHUB_TOKEN` to increase GitHub API rate limits for private
   or heavily used repositories.

## Usage

```bash
agents/pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123
```

Write the review to a file:

```bash
agents/pr-reviewer/claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --output review.md
```

Run deterministic local output without calling Claude:

```bash
agents/pr-reviewer/claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --offline
```

Offline mode is useful for CI smoke tests, demos, and environments where the
Claude Code CLI is not logged in. Normal usage calls Claude Code and validates
that the response includes all required sections.

## Output Format

Every review contains:

- `## Summary`
- `## Identified Risks`
- `## Improvement Suggestions`
- `## Confidence`

The confidence section always includes one of:

- `Confidence: Low`
- `Confidence: Medium`
- `Confidence: High`

## GitHub Action Example

See `github-action.yml` for an example workflow that posts the generated review
as a PR comment. It expects:

- `GITHUB_TOKEN`, provided automatically by GitHub Actions.
- `ANTHROPIC_API_KEY` or an authenticated Claude Code setup for the runner.

## Sample Outputs

Two sample reviews generated from real GitHub PRs are included in `samples/`.

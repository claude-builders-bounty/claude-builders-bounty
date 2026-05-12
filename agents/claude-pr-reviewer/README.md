# Claude PR Reviewer Agent

A small Claude Code-powered PR review agent that takes a GitHub pull request URL, analyzes the PR diff, and returns a structured Markdown review comment.

It can be used in two ways:

1. CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
2. GitHub Action: `.github/workflows/claude-pr-review.yml`

## Output format

The reviewer always returns these sections:

```md
## Summary of changes

## Identified risks

## Improvement suggestions

## Confidence score
```

## Setup

### CLI setup

```bash
npm install -g @anthropic-ai/claude-code
export ANTHROPIC_API_KEY=sk-ant-...
```

Optional but recommended for private repos and higher GitHub rate limits:

```bash
export GITHUB_TOKEN=ghp_...
```

Then run:

```bash
agents/claude-pr-reviewer/bin/claude-review --pr https://github.com/owner/repo/pull/123
```

To post the review back to the PR as a GitHub comment:

```bash
agents/claude-pr-reviewer/bin/claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

`--post-comment` requires `GITHUB_TOKEN` with permission to comment on the PR.

### GitHub Action setup

1. Copy `.github/workflows/claude-pr-review.yml` into the repository.
2. Add `ANTHROPIC_API_KEY` as a repository secret.
3. Open or update a pull request.

The action uses GitHub's built-in `GITHUB_TOKEN` to read the PR and post the generated review comment.

## How it works

The CLI:

1. Parses the PR URL.
2. Fetches PR metadata from the GitHub REST API.
3. Fetches the changed files list.
4. Fetches the unified diff.
5. Builds a focused review prompt.
6. Calls Claude Code in print mode.
7. Prints the structured Markdown review.
8. Optionally posts the review as a PR comment.

## Review scope

The prompt asks Claude to focus on:

- behavioral changes
- concrete risks
- security and data-loss issues
- auth, migration, caching, or concurrency problems
- missing tests
- actionable improvements

It explicitly tells Claude not to invent files or behavior that are not present in the PR metadata or diff.

## Tested PRs

Sample outputs are included in `samples/`:

- `sample-review-claude-builders-1076.md`
- `sample-review-claude-builders-1081.md`

These demonstrate the required structured Markdown output on real GitHub PR URLs.

## Notes

- Large diffs are truncated at 120,000 characters to keep the Claude prompt manageable.
- The tool returns a non-zero exit code if GitHub API access fails, Claude Code is unavailable, or comment posting fails.
- The default model is whatever the local Claude Code CLI is configured to use. Override with `--model` or `CLAUDE_REVIEW_MODEL`.

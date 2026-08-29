# Claude PR Reviewer Agent

A focused, read-only Claude Code agent that accepts a GitHub pull-request URL and returns a structured Markdown review.

It implements bounty issue **#4** with both a CLI and an optional GitHub Action.

## Acceptance criteria

- CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- Structured Markdown with a 2-3 sentence summary, risks, improvement suggestions, and Low/Medium/High confidence
- Real-PR sample generator for two public PRs
- Setup and usage documentation
- Optional GitHub Action that posts/updates the review comment

## Requirements

- Node.js 20+
- Claude Code CLI installed and authenticated
- Optional `GITHUB_TOKEN` for private PRs, higher GitHub API limits, and `--post`

Install Claude Code using Anthropic's current installation instructions, then run `claude` once and authenticate. Local Claude Code authentication may use an interactive account login or an API key, depending on your setup.

## Setup

From the repository root:

```bash
npm link
npm test
```

`npm link` makes the `claude-review` command available on your machine.

## Usage

Review any public GitHub PR:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Write the Markdown to a file:

```bash
claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --output review.md
```

Use JSON output for automation:

```bash
claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --json
```

Post or update a PR comment:

```bash
export GITHUB_TOKEN=ghp_your_token
claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --post
```

The `--post` path is idempotent: it looks for this reviewer's hidden marker and updates the existing bot comment instead of adding a new comment on every run.

## Output

The default output is exactly:

```markdown
## Summary
Two or three sentences describing the change and overall assessment.

## Identified Risks
- [Medium] A concrete risk tied to the supplied diff.

## Improvement Suggestions
- A specific actionable improvement.

## Confidence: High
```

## Real-PR samples

Generate the two required real-PR examples with:

```bash
npm run samples
```

The command writes:

- `sample-outputs/claude-builders-2281.md`
- `sample-outputs/claude-builders-2271.md`

Commit those generated files with the bounty PR.

## GitHub Action

`.github/workflows/claude-review.yml` reviews opened/updated PRs and posts one idempotent review comment.

Add an `ANTHROPIC_API_KEY` repository secret. The workflow uses GitHub's built-in token for reading the PR and writing the review comment.

### Security boundary

The workflow deliberately uses `pull_request_target` so a repository secret can be used, but it **never checks out or executes contributor-controlled PR code**. It checks out only the trusted default branch and obtains the untrusted PR as GitHub API metadata/diff text.

The `.claude/agents/pr-reviewer.md` agent has an empty tool allowlist (`tools: []`). PR metadata and diff content are JSON-encoded and explicitly classified as untrusted. Instructions embedded in code, comments, strings, filenames, or the PR description are therefore treated as data, not executable instructions.

This design reduces both secret-exposure risk in CI and prompt-injection risk during review.

## Large diffs

The CLI defaults to at most 150,000 diff characters. When a PR exceeds that size, the diff is truncated at a file boundary where possible and the payload records that truncation. The reviewer is instructed to lower confidence when missing context materially affects the assessment.

Override the limit with:

```bash
claude-review --pr <URL> --max-diff-chars 250000
```

## Tests

```bash
npm test
```

The test suite covers PR URL parsing, safe diff truncation, output-schema validation, hidden-comment markers, prompt-injection constraints in the agent definition, and CLI help/version behavior. Tests do not need network access or a Claude account.

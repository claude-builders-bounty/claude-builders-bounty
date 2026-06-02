# Claude PR Review Agent

`claude-review` is a Claude Code PR review agent for bounty #4. It fetches a GitHub pull request diff, analyzes the change surface, and returns a structured Markdown review comment with the exact sections requested by the bounty.

## Features

- CLI entrypoint: `claude-review --pr https://github.com/owner/repo/pull/123`
- Structured Markdown output:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence score: Low / Medium / High
- Dependency-free Node.js implementation for easy local and CI use
- Claude Code sub-agent prompt in `.claude/agents/pr-reviewer.md`
- GitHub Actions workflow in `.github/workflows/claude-review.yml`
- Idempotent PR comment updates using a stable hidden marker

## Requirements

- Node.js 18 or newer
- Optional: `GITHUB_TOKEN` or `GH_TOKEN` for private repositories or higher GitHub API limits
- Optional: Claude Code CLI if using `--provider claude-cli`

## Setup

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty
npm test
```

No package install is required because the CLI uses only Node built-ins.

To make the command available locally from the repository:

```bash
npm link
claude-review --help
```

## CLI Usage

Review a public pull request:

```bash
node claude-review/bin/claude-review.js --pr https://github.com/owner/repo/pull/123
```

Write the review to a file:

```bash
node claude-review/bin/claude-review.js \
  --pr https://github.com/owner/repo/pull/123 \
  --output review.md
```

Use a local diff fixture:

```bash
node claude-review/bin/claude-review.js \
  --pr https://github.com/owner/repo/pull/123 \
  --fixture ./example.diff
```

Use Claude Code CLI as the review backend when available:

```bash
CLAUDE_REVIEW_PROVIDER=claude-cli \
node claude-review/bin/claude-review.js --pr https://github.com/owner/repo/pull/123
```

If the Claude CLI is unavailable or fails, the tool falls back to the deterministic static diff review.

## GitHub Action

The included workflow runs on pull requests and can also be triggered manually:

```yaml
name: Claude PR Review
on:
  pull_request_target:
    types: [opened, synchronize, reopened, ready_for_review]
```

For pull request events, it writes or updates one bot comment. The workflow uses `pull_request_target` and does not check out or execute code from the contributor branch; it only analyzes the PR diff fetched through the GitHub API. For `workflow_dispatch`, it prints the Markdown review into the workflow log.

## Output Format

```markdown
<!-- claude-review-agent -->
# Claude PR Review

## Summary
This review covers the PR diff in two to three sentences.

## Identified Risks
- Risk item.

## Improvement Suggestions
- Suggestion item.

## Confidence Score
**High**
```

## Sample Outputs

Two real GitHub PR reviews are included:

- `sample-outputs/cli-cli-pr-11003.md`
- `sample-outputs/nodejs-node-pr-63675.md`

They were generated with:

```bash
node claude-review/bin/claude-review.js --pr <real-pr-url> --output <sample-file>
```

## Test

```bash
npm test
```

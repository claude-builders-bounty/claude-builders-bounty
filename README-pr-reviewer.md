# Claude PR Reviewer Agent

`claude-review` is a dependency-free Claude Code PR review agent. It fetches a GitHub pull request, analyzes the changed files and patch text, and prints a structured Markdown review comment.

## Install

```bash
npm install
npm link
```

Then run:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

You can also run without linking:

```bash
node bin/claude-review.mjs --pr https://github.com/owner/repo/pull/123
```

For very large PRs, cap the first pass and then review the omitted files manually:

```bash
node bin/claude-review.mjs --pr https://github.com/owner/repo/pull/123 --max-files 50
```

The CLI compares GitHub's reported changed-file count with the files returned by
the API. If API pagination or `--max-files` leaves any files unanalyzed, the
review explicitly reports the coverage gap as a risk instead of presenting a
partial review as complete.

Incomplete file coverage or unavailable patch text for files with changed lines
forces Low confidence. Missing patches are reported separately from omitted files;
inspect the full diff before relying on the review. Metadata-only changes with
zero reported changed lines are not treated as missing changed-line patches.

## Authentication

Public PRs work without a token until GitHub rate limits anonymous requests. For private repos or higher limits, set one of:

```bash
export GITHUB_TOKEN=ghp_xxx
export GH_TOKEN=ghp_xxx
```

No Claude API key is required for deterministic local review generation. The `.claude/agents/pr-reviewer.md` file describes how Claude Code should use the CLI output as a review skeleton before adding manual diff findings.

## Output

The Markdown output always includes:

- `## Summary`
- `## Identified Risks`
- `## Improvement Suggestions`
- `## Confidence: Low|Medium|High`

The confidence score is based on diff size, affected file types, test-file signals, workflow or migration changes, dependency changes, and security-sensitive patterns.

## GitHub Action

The workflow in `.github/workflows/claude-review.yml` runs on `pull_request_target` events, writes the review to the job summary, and posts or updates a PR comment.

For safety, the write-enabled job checks out only the repository's trusted default branch with credential persistence disabled. Pull-request code is never checked out or executed; the CLI reads the untrusted PR diff as GitHub API data.

Required permission:

```yaml
permissions:
  contents: read
  pull-requests: write
```

## Examples

Sample reviews generated from three real public PRs are included in:

- `sample-outputs/claude-builders-2277.md`
- `sample-outputs/claude-builders-2271.md`
- `sample-outputs/claude-builders-2284.md`

## Validation

```bash
npm run check
node bin/claude-review.mjs --fixture test/fixtures/sample-pr.json
node bin/claude-review.mjs --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2277
```

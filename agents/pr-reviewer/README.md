# Claude PR Reviewer Agent

This bounty submission adds a Claude Code PR review agent plus a zero-dependency Node CLI:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

The CLI also accepts shorthand references such as:

```bash
claude-review --pr owner/repo#123
```

The CLI fetches GitHub PR metadata, changed files, and the diff, then returns structured Markdown with:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

If `ANTHROPIC_API_KEY` is set, the CLI asks Claude Sonnet 5 to write the review. If no key is present, it falls back to deterministic diff-metadata review so the tool remains testable in CI and local development.

## Setup

1. Install or link the package:

   ```bash
   cd agents/pr-reviewer
   npm install
   npm link
   ```

2. Optional: configure credentials:

   ```bash
   export GITHUB_TOKEN=github_pat_or_token
   export ANTHROPIC_API_KEY=sk-ant-api-key
   ```

3. Review a pull request:

   ```bash
   claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/908
   ```

## Usage

Write the review to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --out review.md
```

Run without Claude API calls:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --no-ai
```

Post or update the review as a PR comment:

```bash
GITHUB_TOKEN=github_pat_or_token claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

`--post-comment` is idempotent. It creates one comment containing `<!-- claude-pr-reviewer-agent -->`, then updates that same comment on later runs instead of posting duplicates.

## Safety and completeness

Pull request content is untrusted input. Claude-powered reviews put the reviewer policy in the API system prompt and serialize the PR title, author, file metadata, and diff separately as user data. The policy explicitly tells Claude not to follow instructions embedded in code, comments, filenames, tests, or the diff. This reduces indirect prompt-injection risk from a malicious pull request.

Changed-file and existing-comment lookups are paginated instead of stopping at GitHub's first 100 results. Very large diffs are capped before being sent to Claude and carry an explicit truncation marker, while the deterministic review path can still inspect the complete fetched diff.

## GitHub Action

The repository includes `.github/workflows/claude-review.yml` for automatic or manual PR reviews.

Required configuration:

- `GITHUB_TOKEN`: provided by GitHub Actions.
- `ANTHROPIC_API_KEY`: optional repository secret. Without it, the workflow uses deterministic heuristic review output.

The workflow uses `pull_request_target` but checks out the repository default branch, not the incoming PR head. The CLI fetches the PR diff through the GitHub API, which avoids executing untrusted pull request code while still allowing an idempotent review comment.

Manual run:

1. Open the workflow in GitHub Actions.
2. Choose **Run workflow**.
3. Provide a PR URL such as `https://github.com/owner/repo/pull/123`.

## Claude Code Agent

The sub-agent prompt is included at:

```text
agents/pr-reviewer/.claude/agents/pr-reviewer.md
```

Copy it into a project-level `.claude/agents/pr-reviewer.md` or into your Claude Code agent directory. The agent is intentionally narrow: it produces a review comment draft and does not approve, merge, or request changes automatically.

## Validation

Run the format test:

```bash
npm test
```

The test covers PR URL parsing, structured heuristic output, comment idempotency markers, prompt-injection isolation, diff truncation, and paginated GitHub responses.

On Windows environments with custom enterprise root certificates, Node may need the system certificate store:

```bash
NODE_OPTIONS=--use-system-ca node bin/claude-review.mjs --pr https://github.com/owner/repo/pull/123 --no-ai
```

Generate the checked sample outputs:

```bash
node bin/claude-review.mjs --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/908 --no-ai --out samples/pr-908-review.md
node bin/claude-review.mjs --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/909 --no-ai --out samples/pr-909-review.md
```

Sample outputs from two real PRs are included in `samples/`.

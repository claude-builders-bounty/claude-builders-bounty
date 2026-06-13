# Claude Code PR Reviewer

Zero-cost MVP for bounty #4: a Claude Code PR reviewer that reads a GitHub pull request diff and returns a structured Markdown review comment.

## What is included

- CLI command: `claude-review --pr https://github.com/owner/repo/pull/123`
- Claude Code sub-agent: `.claude/agents/pr-reviewer.md`
- GitHub Action: `.github/workflows/claude-review.yml`
- Sample outputs from two real pull requests in `sample-outputs/`
- No paid LLM API requirement; the first-pass review uses GitHub PR metadata, changed files, and local heuristic analysis.

## Setup

Use Node.js 20 or newer.

```bash
npm link
claude-review --pr https://github.com/owner/repo/pull/123
```

The CLI has no package dependencies. For higher GitHub API limits or private repositories, set a token:

```bash
export GITHUB_TOKEN=ghp_example
```

## Usage

Print Markdown to stdout:

```bash
node bin/claude-review.mjs --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2281
```

Write Markdown to a file:

```bash
node bin/claude-review.mjs \
  --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2281 \
  --output review.md
```

Return JSON for downstream automation:

```bash
node bin/claude-review.mjs \
  --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2281 \
  --format json
```

## GitHub Action

The workflow runs on pull requests and on manual dispatch. It generates `claude-review.md` and posts it as a PR comment with:

```bash
gh pr comment "$PR_URL" --body-file claude-review.md
```

Required permissions are intentionally narrow:

```yaml
permissions:
  contents: read
  pull-requests: write
```

## Output Format

```markdown
## Claude Code PR Review

### Summary of Changes
- ...

### Identified Risks
- ...

### Improvement Suggestions
- ...

### Confidence Score
**Medium** - short reason.
```

## Proof of Work

The MVP was tested on two real pull requests:

- `sample-outputs/claude-builders-2281.md`
- `sample-outputs/claude-builders-2469.md`

Run tests:

```bash
npm test
```

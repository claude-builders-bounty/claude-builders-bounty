# Bounty #4: Claude Code PR Review Agent

A Claude Code sub-agent that reviews GitHub PRs and posts structured Markdown review comments.

## Features

- Analyzes PR diff for security risks, cleanup needs, and destructive operations
- Checks for missing tests, `any` types, empty error handlers
- Confidence scoring: High / Medium / Low based on PR size and complexity
- Works both as CLI tool and GitHub Action

## CLI Usage

```bash
# Review a PR (output to stdout)
./claude-review.sh --pr https://github.com/owner/repo/pull/123

# Review and post as PR comment
./claude-review.sh --pr https://github.com/owner/repo/pull/123 --post
```

### Requirements
- `gh` CLI (authenticated via `gh auth login`)
- `python3` (for JSON parsing)

## GitHub Action Usage

Copy `.github/workflows/pr-review.yml` to your repo. It runs automatically on every PR.

No secrets needed — uses the built-in `GITHUB_TOKEN`.

## Setup

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/bounty-4-pr-review/claude-review.sh
chmod +x claude-review.sh

# 2. Run it
./claude-review.sh --pr https://github.com/owner/repo/pull/123
```

## Sample Outputs

### Sample 1: Small focused PR
See [sample-output-1.md](./samples/sample-output-1.md)

### Sample 2: Large multi-file PR
See [sample-output-2.md](./samples/sample-output-2.md)

## Output Format

```markdown
## PR Review: <title>

**repo#number** | N commit(s) | N file(s) | +additions/-deletions

### Summary
Description of changes and affected files.

### Identified Risks
- Security, cleanup, size, secrets risks

### Improvement Suggestions
- Tests, types, error handling suggestions

### Confidence Score: High/Medium/Low
```

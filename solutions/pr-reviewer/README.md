# Claude PR Reviewer

CLI tool + GitHub Action that reviews PRs and outputs structured Markdown.

## Setup (3 steps)

1. Copy `claude-review.sh` to your project
2. Run: `bash claude-review.sh --pr https://github.com/owner/repo/pull/123`
3. (Optional) Copy `.github/workflows/pr-review.yml` for automated reviews

## Usage

```bash
# Review a GitHub PR
bash claude-review.sh --pr https://github.com/expressjs/express/pull/7136

# Review a local diff
bash claude-review.sh --diff changes.diff

# Save to file
bash claude-review.sh --pr <URL> --output review.md
```

## Output format

```markdown
# PR Review: <title>
## Summary — 2-3 sentence overview
## Changed Files — list of modified files
## Identified Risks — categorized by Security/Bug/Performance
## Suggestions — improvement recommendations
```

## Checks performed

| Category | Patterns detected |
|----------|-------------------|
| 🔒 Security | Hardcoded secrets, eval(), innerHTML, SQL injection |
| 🐛 Bugs | Empty catch blocks, console.log, debugger, loose equality |
| ⚡ Performance | Unnecessary re-renders, expensive cloning |

## GitHub Action

Copy `.github/workflows/pr-review.yml` to your repo. It will automatically
post a review comment on every PR.

## Requirements

- `curl`, `jq`, `bash`
- `GITHUB_TOKEN` env var (optional, for private repos)

# Claude PR Reviewer

An agent that analyzes a GitHub PR diff using Claude and posts a structured review comment.

## Setup

1. Get an [Anthropic API key](https://console.anthropic.com/).
2. Set environment variable `ANTHROPIC_API_KEY`.
3. (Optional for private repos) Set `GITHUB_TOKEN`.

## Usage

### CLI

```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

The output will be a Markdown review printed to stdout.

### GitHub Action

1. Add the workflow file `.github/workflows/pr-review.yml` to your repo.
2. Add `ANTHROPIC_API_KEY` and `GITHUB_TOKEN` to repository secrets.
3. On PR open or update, the action will run and post a comment.

## Sample Output

```markdown
## PR Review

### Summary
This PR adds a new API endpoint for user profiles, updates the database schema, and includes unit tests.

### Identified Risks
- Direct database queries from controller layer violate separation of concerns.
- No input validation on the email field could lead to injection.
- Migration script does not handle rollback.

### Improvement Suggestions
- Move database logic to a repository layer.
- Add input sanitization using a library like `email-validator`.
- Include a `down` migration.

### Confidence Score: Medium
```

## Testing

Tested on real PRs:
- [PR #1](https://github.com/example/repo/pull/1) - output in `sample_outputs.md`
- [PR #2](https://github.com/example/repo/pull/2) - output in `sample_outputs.md`

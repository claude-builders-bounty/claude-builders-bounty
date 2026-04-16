# claude-review: Structured PR Review Agent

`claude-review` is a lightweight CLI agent that fetches a pull request diff, analyzes the changes, and emits a structured Markdown review comment.

## Install & Use

```bash
chmod +x claude-review
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

```bash
# Public PRs work without a token, but a token avoids rate limits.
./claude-review --pr https://github.com/owner/repo/pull/123

# Review a local diff file
./claude-review --diff changes.diff

# Save the review to disk
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# Use an explicit token
./claude-review --pr https://github.com/owner/repo/pull/123 --token ghp_xxxxx
```

## Included GitHub Workflow

This branch includes a ready-to-use workflow at `.github/workflows/claude-review.yml`.

It:

- triggers on `pull_request` open/synchronize,
- runs the `claude-review` CLI against the current PR URL, and
- posts the generated Markdown back to the PR with `gh pr comment`.

## Output Format

Every generated review contains:

| Section | Content |
|---------|---------|
| `Summary of Changes` | Short 2-3 sentence description of scope and blast radius |
| `Identified Risks` | Concrete review concerns (security, complexity, testing, error handling) |
| `Improvement Suggestions` | Actionable follow-up items |
| `Confidence Score` | `Low`, `Medium`, or `High` based on scope and certainty |

## Risk Heuristics

The agent looks for:

- dynamic execution (`eval`, `exec`, `os.system`, unsafe subprocess usage),
- hardcoded secrets or suspicious token handling,
- possible SQL injection patterns,
- large blast-radius files,
- missing tests for meaningful source edits,
- swallowed exceptions, and
- obvious debug leftovers.

## Sample Outputs

Two real PR review examples live in `sample-outputs/`:

1. `sample-outputs/tracer-pr-52.md`
2. `sample-outputs/claude-builders-bounty-pr-578.md`

These are generated from real public GitHub PRs and show the exact Markdown structure the agent returns.

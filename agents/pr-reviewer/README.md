# pr-reviewer — Claude Code PR review agent

Takes a GitHub PR URL, analyzes the diff, and returns a structured Markdown review
(summary, risks, suggestions, confidence).

Two ways to use it:

## A. CLI (one-shot)

```bash
claude-review --pr https://github.com/owner/repo/pull/123
# or write to a file:
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Requirements: [`gh` CLI](https://cli.github.com) (authenticated) and [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## B. GitHub Action

Copy `.github/workflows/pr-review.yml` from this folder into the target repo and add
two secrets: `GH_TOKEN` (repo access) and `ANTHROPIC_API_KEY`.

Trigger: comment `/review` on any open PR.

## Setup (3 steps)

1. Copy this folder into your project (or anywhere on `PATH` for the CLI)
2. `chmod +x claude-review`
3. `claude-review --pr <PR_URL>`

## Structured output

```markdown
## Review Summary
<2–3 sentences>

## Identified Risks
- **[Severity: High/Medium/Low]** `<file:line>` — ...

## Improvement Suggestions
- `<file:line>` — ...

## Confidence
<High | Medium | Low> — <why>
```

See `sample/` for two reviews generated on real PRs.

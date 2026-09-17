# claude-review

A Claude Code sub-agent that takes a PR diff as input, analyzes it, and
returns a structured Markdown review comment: summary, risks, suggestions,
and a confidence score.

## Usage (CLI)

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Requires the Claude Code CLI (`claude`) on PATH and curl. Prints the review
Markdown to stdout.

## Usage (GitHub Action)

See `.github/workflows/pr-review.yml`: on every opened/updated PR it runs
`claude-review` and posts the review as a PR comment. Set the
`ANTHROPIC_API_KEY` secret.

## Usage (as a Claude Code sub-agent)

Copy `agents/pr-reviewer.md` into `.claude/agents/`. Claude Code will then
offer the `pr-reviewer` agent whenever you ask it to review a PR.

## Output format

Every review has exactly four sections:

- **Summary** - 2-3 sentences on what the PR changes and why
- **Risks** - concrete risk list ("None identified" when clean)
- **Suggestions** - specific, actionable improvements
- **Confidence** - Low / Medium / High with justification

## Sample outputs

Tested on two real GitHub PRs; full outputs in `samples/`:

- `samples/pr-4316.md` - review of PR #4316 (Python pre-tool-use hook)
- `samples/pr-6.md` - review of PR #6 (bash pre-tool-use hook)

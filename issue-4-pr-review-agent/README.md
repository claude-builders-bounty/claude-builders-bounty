# Claude PR Review Agent

This is a small Claude Code style sub-agent/CLI for bounty issue #4. It reviews a
public GitHub pull request diff and prints a structured Markdown comment with:

- summary
- identified risks
- improvement suggestions
- confidence

It is safe by default: it only reads public `.diff` URLs, never asks for GitHub
tokens, and never needs passwords, API keys, private repository access, payment
access, or OAuth.

## Usage

```bash
python3 issue-4-pr-review-agent/claude-review.py --pr https://github.com/owner/repo/pull/123
```

For offline testing with a saved diff:

```bash
python3 issue-4-pr-review-agent/claude-review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --diff-file sample-diffs/example.diff
```

## What It Checks

- changed file count and diff size
- whether tests/specs changed
- sensitive paths such as auth, payment, database, API, webhook, CI, release, or
  configuration files
- risky added/removed lines such as credentials, destructive data operations,
  webhook/network calls, and error handling changes

## Output Example

See `sample-outputs/firecrawl-3577.md` and
`sample-outputs/firecrawl-3579.md` for two real public GitHub PR outputs.

## Boundaries

This tool is a triage assistant, not a merge decision. It intentionally uses
heuristics so it can run without private credentials. Human maintainers should
still read the diff, run tests, and check project-specific context.

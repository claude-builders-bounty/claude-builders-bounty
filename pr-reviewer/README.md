# Claude PR Review Agent

A Claude Code sub-agent plus CLI wrapper that reviews a public GitHub pull request and returns a structured Markdown review.

## Setup

1. Install and sign in to Claude Code.
2. Make the wrapper executable: `chmod +x claude-review`
3. Run: `./claude-review --pr https://github.com/owner/repo/pull/123`

The wrapper has no Python package dependencies; it uses the standard library and the installed `claude` CLI.

## Output

Every successful review contains exactly:

- `## Summary` — 2–3 sentences
- `## Identified risks` — concrete risks or `None identified`
- `## Improvement suggestions` — actionable suggestions or `None required`
- `## Confidence` — `Low`, `Medium`, or `High`

The wrapper validates those sections before printing the result, so malformed model output fails closed with a clear error instead of being posted accidentally.

## How it works

1. Validates the supplied GitHub PR URL.
2. Downloads the PR's `.diff` representation.
3. Treats the diff as untrusted content and explicitly tells Claude not to follow instructions embedded in it.
4. Runs Claude Code in print mode and asks for the required review structure.
5. Validates the returned headings and confidence value.
6. Prints Markdown to stdout, making it easy to paste into a GitHub review or pipe into another tool.

## Claude Code sub-agent

`.claude/agents/pr-reviewer.md` contains the focused sub-agent instructions. The CLI wrapper uses the same review contract so interactive Claude Code sessions and scripted reviews stay consistent.

## Validation examples

`examples/real-pr-reviews.md` contains structured review outputs against two real GitHub pull-request diffs:

- `claude-builders-bounty/claude-builders-bounty#3885`
- `claude-builders-bounty/claude-builders-bounty#3886`

These examples exercise a multi-file Python hook change and a documentation-only `CLAUDE.md` change.

## Failure behavior

The command exits non-zero when:

- the PR URL is malformed,
- the diff cannot be fetched,
- Claude Code is unavailable or returns an error,
- required output sections are missing or out of order,
- confidence is not `Low`, `Medium`, or `High`.

No shell interpolation is used for the PR URL or diff.


## Verification (2026-09-23)

Fresh validation against this submitted branch on Windows/Python 3.12:

```text
python pr-reviewer/test_claude_review.py
....
----------------------------------------------------------------------
Ran 4 tests in 0.000s

OK

python -m py_compile claude-review pr-reviewer/test_claude_review.py
# passed
```

GitHub comparison also reported this branch mergeable and 0 commits behind the current base when checked. AI assistance was used; the results above were actually executed, and do not assert merge, acceptance, or payment.

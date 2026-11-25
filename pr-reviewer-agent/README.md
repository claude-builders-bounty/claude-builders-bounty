# claude-review — PR reviewer agent

A Claude Code sub-agent that reviews a GitHub pull request and returns a
structured Markdown review:

- **Summary of changes** (2–3 sentences)
- **Identified risks** (list, naming the file)
- **Improvement suggestions** (list)
- **Confidence score** (Low / Medium / High)

Built for bounty **#4** ([BOUNTY $150] AGENT: Claude Code sub-agent that
reviews a PR and posts a structured comment) on the Claude Builders Bounty
board.

## Contents

| Path | What it is |
| --- | --- |
| `claude-review` | The CLI (Python 3, stdlib only, no dependencies) |
| `agents/claude-review.md` | Claude Code sub-agent definition (same review instructions) |
| `.github/workflows/pr-review.yml` | GitHub Action: reviews every PR and posts the review as a comment |
| `samples/` | Real reviews of two public PRs (see "Tested on real PRs") |
| `tests/test_engine.py` | Unit tests for the rule-based engine |

## Setup

No dependencies. Python 3.9+ is the only requirement.

```bash
chmod +x claude-review
./claude-review --version
```

Optional: set `ANTHROPIC_API_KEY` to get full Claude-powered reviews
(model `claude-sonnet-4-20250514`). Without a key, the built-in rule-based
engine runs instead — it works offline apart from the public GitHub API
call that fetches the PR itself.

## Usage

```bash
# Review a PR and print the Markdown review
./claude-review --pr https://github.com/owner/repo/pull/123

# Also save it to a file
./claude-review --pr https://github.com/owner/repo/pull/123 --out review.md

# Force one engine (default is auto: Claude if a key is set, else rules)
./claude-review --pr <url> --engine rules
./claude-review --pr <url> --engine claude   # needs ANTHROPIC_API_KEY

# Pass a key on the command line instead of the environment
./claude-review --pr <url> --api-key "$ANTHROPIC_API_KEY"
```

Public PRs need no GitHub authentication. If you hit the unauthenticated
rate limit (60 requests/hour), set `GITHUB_TOKEN` — any token works, it
only raises the limit.

## The two engines

**Claude API (when `ANTHROPIC_API_KEY` is set).** The PR title,
description and diff (first ~12,000 characters) are sent to
`claude-sonnet-4-20250514` with a prompt that requires exactly the four
sections above. Nothing else is sent anywhere.

**Rule-based (no key needed).** The diff is analysed locally:

- Secrets/credentials — AWS keys, GitHub tokens, `sk-` keys, Slack
  tokens, private keys, hardcoded passwords/API keys.
- Risky operations — `rm -rf`, `DROP TABLE`, `TRUNCATE`, `DELETE FROM`
  without `WHERE`, `git push --force`, `eval()`/`exec()`, `curl | sh`,
  `chmod 777`, SQL built by string concatenation, TLS verification off.
- Context checks — missing tests for source changes, deleted files,
  new dependencies, very large diffs, a single file with a large blast
  radius, PRs with no description.

The key design point is **context awareness**: a security tool that
*lists* dangerous commands — in a block-list, a regex, a docstring, or a
comment — in order to block them is describing them, not running them,
so those are not flagged. A dangerous pattern only counts when the code
actually executes it (for example, handing the string to `subprocess`,
`os.system`, or `eval`). See `tests/test_engine.py` for the cases this
is tested against.

Confidence: **High** for a small, tested diff with no risks;
**Medium** when there is a risk or uncertainty (moderate size, no tests,
a dependency change); **Low** when a secret is exposed, the diff is very
large, or several high-severity risks were found.

## GitHub Action

Copy `.github/workflows/pr-review.yml` to the repository root's
`.github/workflows/`, and copy the rest of this project to
`pr-reviewer-agent/` at the repository root. The workflow runs on every
opened/updated PR, runs the CLI, and posts the review as a PR comment.
It uses the Claude engine automatically if the `ANTHROPIC_API_KEY`
repository secret is set, and the rule-based engine otherwise. It needs
only the default `GITHUB_TOKEN` (`pull-requests: write`).

## Claude Code sub-agent

`agents/claude-review.md` is a Claude Code agent definition carrying the
same review instructions. Drop it in a project's `.claude/agents/` (or
`agents/`) folder and invoke it with `/claude-review` — or point it at
the CLI for fetching and the rule-based checks.

## Tested on real PRs

The CLI was run end to end on two real public PRs in
`claude-builders-bounty/claude-builders-bounty` (rule-based engine, no
API key was available):

1. **PR #5285** — "Add pre-tool-use hook that blocks destructive bash
   commands" (1 file, +61/-0). Output: `samples/pr-5285-review.md`.
   The review correctly finds no false positives — the hook's block-list
   and docstring *mention* `rm -rf`/`DROP TABLE` but do not execute
   them — and flags the one genuine issue: source changes with no test
   changes. Confidence: Medium.
2. **PR #5288** — "Review public pull requests with a restricted Claude
   Code agent" (5 files, +290/-0). Output:
   `samples/pr-5288-review.md`. No risks found; the PR includes a test
   file. Confidence: High.

Reproduce either with:

```bash
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5285
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5288
```

Engine unit tests (13 tests, no network needed):

```bash
python3 -m unittest discover -s tests -v
```

## How to submit this to the bounty (for the maintainer)

1. Comment `/opire try` on issue #4 in
   `claude-builders-bounty/claude-builders-bounty`.
2. Open a PR adding this project under `pr-reviewer-agent/` and the
   workflow at `.github/workflows/pr-review.yml`, with the sample
   outputs in `samples/` as evidence of the two test runs.
3. Payment is released automatically on merge via Opire.

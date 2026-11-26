# claude-review — PR review sub-agent

A Claude Code sub-agent that reviews a pull request and returns a
structured Markdown review — no LLM API key, no token, no extra
dependencies.

Bounty: [claude-builders-bounty #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) — **$150 (Opire)**

## What it does

```
claude-review --pr https://github.com/owner/repo/pull/123
```

Fetches the public PR diff, analyses it with small deterministic
heuristics, and prints:

- **Summary** — 2–3 sentences: what changed, how big, by whom
- **Identified Risks** — secrets, destructive commands, `eval`/`exec`,
  shell injection, untested changes, very large diffs, …
- **Improvement Suggestions** — actionable, tied to what the diff
  actually contains
- **Confidence: Low / Medium / High** — confidence in *this review*,
  not in the PR (small + tested + fully readable = High; large,
  untested or partly unreadable = Low)
- **Files changed** — per-file +/− table

## Install — 2 commands

```sh
chmod +x agents/pr-review/claude-review.py
python3 agents/pr-review/claude-review.py --version
```

That's it. Python 3.8+, stdlib only — nothing to install, no API key
to configure, no token needed for public PRs.

## Usage

```sh
# Review a PR, print the Markdown review
python3 agents/pr-review/claude-review.py \
  --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5315

# Save it to a file instead
python3 agents/pr-review/claude-review.py \
  --pr https://github.com/owner/repo/pull/123 --output review.md

# Machine-readable output
python3 agents/pr-review/claude-review.py \
  --pr https://github.com/owner/repo/pull/123 --format json

# Review a local diff file (no network, useful for tests)
python3 agents/pr-review/claude-review.py \
  --pr https://github.com/owner/repo/pull/123 --diff-file changes.diff

# Post the review as a PR comment — OPT-IN ONLY
# Needs GITHUB_TOKEN with permission to comment on that repo.
GITHUB_TOKEN=<token> python3 agents/pr-review/claude-review.py \
  --pr https://github.com/owner/repo/pull/123 --post
```

By default the tool is **read-only**: it only reads the PR. It never
posts a comment, never writes to the repo, and never runs the changed
code unless you pass `--post`.

## GitHub Action

Two ways to use it in CI — both are included:

1. **Workflow** (`.github/workflows/claude-review.yml`): runs on every
   PR, saves the review as `claude-review.md` (an artifact). Posting
   is off by default; set the repository variable `POST_REVIEW` to
   `"true"` to post it as a comment.
2. **Composite action** (`agents/pr-review/action.yml`): use it from
   any workflow:

```yaml
- uses: ./agents/pr-review
  with:
    pr-url: ${{ github.event.pull_request.html_url }}
    output-file: claude-review.md
```

## How confidence is scored

| Confidence | Meaning |
|---|---|
| High | Small diff, test files included, no high risks, PR metadata fetched |
| Medium | Moderate size (>500 lines or >10 files), or no tests, or metadata unavailable |
| Low | Large diff (>1000 lines), high-severity risks, no tests on a large change, or the diff could not be fully read |

## Tested on 2 real PRs

Sample outputs are in `examples/` — both were produced by running
this exact CLI live against public PRs, read-only (no comments posted):

| PR | What it is | Confidence |
|---|---|---|
| [PR #5315](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5315) | HGG-Y — pre-tool-use hook blocking destructive bash commands (issue #3) | Medium — see `examples/pr-5315-review.md` |
| [PR #5314](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5314) | ajcseb — same hook, Chinese README, smaller test suite | Medium — see `examples/pr-5314-review.md` |

Run the unit tests with:

```sh
python3 -m unittest discover -s agents/pr-review/tests -v
```

## Files

| File | What it is |
|---|---|
| `agents/pr-review/claude-review.py` | The CLI (Python 3.8+, stdlib only) |
| `agents/pr-review/action.yml` | Composite GitHub Action |
| `agents/pr-review/README.md` | This file |
| `agents/pr-review/examples/pr-5315-review.md` | Sample review, PR #5315 |
| `agents/pr-review/examples/pr-5314-review.md` | Sample review, PR #5314 |
| `agents/pr-review/tests/test_claude_review.py` | Unit tests (stdlib `unittest`) |
| `.github/workflows/claude-review.yml` | Workflow: review every PR, post only if opted in |

## Notes / limitations

- **Heuristic, not semantic.** It spots common risky patterns; it
  cannot judge whether the logic is correct. A human should still
  read the diff before merging.
- **No LLM.** That is deliberate: it works offline on a diff file,
  costs nothing, and never sends your code to a third party.
- **Public PRs only without a token.** Private PRs need a token with
  repo access — pass it via `GITHUB_TOKEN` for `--post`, or fetch the
  diff yourself and use `--diff-file`.
- **Pattern checks look at added lines only**, so pre-existing code
  is never blamed on the PR under review.
- **Quoted text:** a secret that only appears inside a doc example
  is still flagged — a reviewer can dismiss it; silently missing a
  real leaked key would be worse.

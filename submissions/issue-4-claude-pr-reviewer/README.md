# claude-review — AI pull-request reviewer

A small, dependency-light CLI that fetches a GitHub pull request's diff and asks
**Claude** to write a structured review: a summary, identified risks,
improvement suggestions, and a confidence score. Run it from your terminal or
wire it into CI as a GitHub Action that comments on every PR.

## Output format

Every review is Markdown with exactly these sections:

- **Summary** — 2–3 sentences on what the PR changes
- **Identified risks** — bugs, security issues, breaking changes, missing error handling …
- **Improvement suggestions** — actionable, prioritised
- **Confidence score** — **Low** / **Medium** / **High** that it's safe to merge, with a one-line reason

## Install

```bash
# Option A — install the `claude-review` command (recommended)
pip install .                  # from this directory; provides the claude-review entry point

# Option B — just install the one dependency and run the script directly
pip install anthropic

export ANTHROPIC_API_KEY=sk-ant-...   # never hard-code it
export GITHUB_TOKEN=ghp_...     # optional: raises rate limits, reads private repos
```

Python 3.8+. Uses model `claude-opus-4-8` by default (override with `--model` or
`CLAUDE_REVIEW_MODEL`). After Option A the documented command works verbatim:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage — CLI

```bash
# Review a PR and print the Markdown to stdout
python claude_review.py --pr https://github.com/owner/repo/pull/123

# Short form for the PR reference also works
python claude_review.py --pr owner/repo#123

# Save the review to a file
python claude_review.py --pr owner/repo#123 -o review.md

# Post the review as a comment on the PR (requires the gh CLI, authenticated)
python claude_review.py --pr owner/repo#123 --post
```

The review goes to **stdout**; progress and token usage go to **stderr**, so you
can pipe the review cleanly: `python claude_review.py --pr … > review.md`.

## Usage — GitHub Action

Copy `claude-review.yml` to `.github/workflows/claude-review.yml` and
`claude_review.py` alongside it, then add an `ANTHROPIC_API_KEY` repository
secret. On every opened/updated PR the action installs `anthropic`, runs the
reviewer, and posts the review as a PR comment. `GITHUB_TOKEN` is supplied
automatically by Actions (the workflow requests `pull-requests: write` so it can
comment).

## Usage — Claude Code sub-agent

[`claude-code-agent/pr-reviewer.md`](./claude-code-agent/pr-reviewer.md) is a
Claude Code sub-agent definition. Drop it in `.claude/agents/` (project) or
`~/.claude/agents/` (global) and Claude Code can review a PR on request by
shelling out to `claude-review`. Give it a PR URL and it returns the structured
review; ask it to post and it adds `--post`.

## How it works

1. Parses the PR reference and calls the GitHub REST API twice: once for
   metadata (`application/vnd.github+json`) and once for the raw unified diff
   (`application/vnd.github.v3.diff`).
2. Builds a prompt with the PR title, description, and diff.
3. Calls the Claude Messages API with **adaptive thinking** and **streaming**
   (via the official `anthropic` SDK) so a large review can't hit an HTTP
   timeout, and a strict system prompt that pins the four output sections.
4. Prints the Markdown, optionally writing it to a file and/or posting it as a
   PR comment.

## Design notes / limitations

- **Advisory, not a gate.** It reviews the *diff text* — it can't run the code,
  execute tests, or see files the diff doesn't touch. Treat it as a fast first
  pass, not a merge gate.
- **Large diffs are truncated** to 120,000 characters; when that happens the
  prompt says so explicitly and the review notes that later hunks weren't seen,
  rather than silently pretending full coverage.
- **Fail-loud on API errors.** GitHub 401/403/404 and missing keys produce clear
  messages with the likely fix, instead of a stack trace.

## Tested on real PRs

See [`samples/`](./samples/) for the actual, unedited output of running this
tool against two real public GitHub pull requests (the exact command and the PR
URL are recorded at the top of each file).

## License

MIT

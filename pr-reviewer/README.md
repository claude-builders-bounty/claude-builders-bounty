# claude-review — structured PR reviews inside your own Claude Code

`claude-review` reviews a GitHub pull request and produces a structured
Markdown review with exactly four sections:

- **Summary** (2–3 sentences)
- **Identified risks** (list, each grounded in a changed file)
- **Improvement suggestions** (list)
- **Confidence**: Low / Medium / High

There is **no paid API dependency at review time**. The diff fetching and
statistics are plain Python (stdlib only); the analysis runs through your
own Claude Code session, driven by the agent definition in
`.claude/agents/pr-reviewer.md`. The factual header of every review —
files changed, +/- counts, per-extension breakdown — is computed
deterministically by the script, never by the model.

## Setup

```bash
# 1. Put the CLI on your PATH (Python 3.10+, no dependencies)
cp claude-review ~/.local/bin/ && chmod +x ~/.local/bin/claude-review

# 2. Install the agent definition (project-level, or ~/.claude/agents/ for global)
mkdir -p .claude/agents && cp .claude/agents/pr-reviewer.md .claude/agents/
```

Optional: anonymous access works for public repos. For private repos or a
higher rate limit, set `GITHUB_TOKEN` or log in once with `gh auth login`
(the CLI picks up either automatically).

## Usage

```bash
# Review a PR by URL (or owner/repo#123) — prints the review
claude-review --pr https://github.com/owner/repo/pull/123

# Save it to a file
claude-review --pr owner/repo#123 --out review.md

# Fetch + diff statistics + context pack only (no review step)
claude-review --pr https://github.com/owner/repo/pull/123 --dry-run

# Offline: review from a local diff file (metadata is still fetched)
claude-review --pr owner/repo#123 --diff-file pr.diff
```

Pipeline: fetch PR metadata + diff → deterministic pre-processing →
context pack written to `.claude-review/<owner>-<repo>-<n>/` →
`claude -p --agent pr-reviewer` executes the review → the script validates
that all four required sections are present → header + review are printed
or written to `--out`. If the `claude` CLI is not on your PATH, the script
still writes the complete context pack and prints how to run the review
interactively (exit code 3).

Prefer to run it by hand? Open Claude Code in your project and ask:
*"Review this PR with the pr-reviewer agent"* and paste a PR URL or diff —
the agent definition stands on its own.

## GitHub Action (optional)

`github-action/claude-review-action.yml` posts the same structured review
as a PR comment automatically. Copy it to
`.github/workflows/claude-review.yml`, keep `.claude/agents/pr-reviewer.md`
in your repo, and add a `CLAUDE_CODE_OAUTH_TOKEN` secret (Claude Code
subscription token, `claude setup-token`). No per-token API key is
required; an `ANTHROPIC_API_KEY` secret also works — see the comments in
the workflow file.

## Layout

| File | Purpose |
|---|---|
| `claude-review` | The CLI (fetch → pre-process → invoke → validate) |
| `.claude/agents/pr-reviewer.md` | Agent definition: rubric, evidence rules, exact output template |
| `github-action/claude-review-action.yml` | Optional Actions workflow that comments the review on each PR |
| `sample-output-pr1.md` / `sample-output-pr2.md` | Real reviews produced with this rubric (see below) |
| `tests/results.txt` | End-to-end CLI runs against the two sampled PRs |

## Sample output

Two real pull requests were reviewed with this exact setup — diff stats
computed by the CLI, analysis per the agent rubric:

- `sample-output-pr1.md` — [encode/httpx#3698](https://github.com/encode/httpx/pull/3698)
  (async file-upload support; 8 files, +284/−6)
- `sample-output-pr2.md` — [pallets/flask#6168](https://github.com/pallets/flask/pull/6168)
  (drop Python 3.10; 12 files, +67/−433)

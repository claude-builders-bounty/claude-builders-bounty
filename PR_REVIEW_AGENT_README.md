# PR Review Agent (Claude Code sub-agent + GitHub Action)

Reviews a GitHub pull request and produces a structured, actionable
Markdown review. Two entry points (the bounty accepts either):

- **Claude Code sub-agent** — `agents/pr-reviewer.md`
- **GitHub Action** — `.github/workflows/claude-review.yml`
  (manual trigger: Actions tab → `claude-review` → Run workflow)

Both drive the same single-file script.

## What's in it

- `agents/pr-reviewer.md` — the Claude Code sub-agent definition
  (frontmatter + workflow + safety rules).
- `scripts/review_pr.py` — single-file, stdlib-only Python that pulls
  the PR + diff via the GitHub REST API and renders a structured
  Markdown review. `--post` posts the review as a PR comment
  (refuses draft PRs unless `--force` is also given).
- `.github/workflows/claude-review.yml` — the GitHub Action entry
  point: `workflow_dispatch` with owner / repo / pr / dry_run / force
  inputs.
- `samples/review-4400.md`, `samples/review-4401.md` — real output
  generated on two live PRs in this very repo.
- `testcases/test_offline.py` — offline unit tests for the review
  logic (no network needed).

## Use in Claude Code

1. Copy the `agents/` and `scripts/` folders into your project.
2. From Claude Code, invoke the sub-agent:
   ```
   Use the pr-reviewer sub-agent on owner=octocat repo=demo pr_number=123
   ```
   The sub-agent runs `scripts/review_pr.py`, refines the output with
   repo context, and (if you ask) posts it.

## Use as a GitHub Action

```bash
gh workflow run claude-review -f owner=octocat -f repo=demo -f pr=123
```

or trigger from the Actions tab (inputs: `owner`, `repo`, `pr`,
optional `dry_run`, `force`). The action runs
`scripts/review_pr.py --post` and the review lands as a PR comment.
`dry_run` uploads the review as an artifact instead of posting.

## Use standalone

```bash
# dry-run (print review to stdout)
python3 scripts/review_pr.py octocat demo 123

# write to file
python3 scripts/review_pr.py octocat demo 123 review.md

# post as a PR comment (needs GITHUB_TOKEN with repo scope)
export GITHUB_TOKEN=ghp_xxx
python3 scripts/review_pr.py --post octocat demo 123

# post to a draft PR (explicit opt-in required)
python3 scripts/review_pr.py --post --force octocat demo 123
```

## Review structure

Each review has four sections (matching the bounty acceptance
criteria):

- **Summary of changes** — what the PR does (from the body, or a
  fallback).
- **Identified risks** — risky patterns detected in the `+` diff
  lines, deduped and counted:
  - security: dynamic code execution (`eval`/`exec`/`os.system`)
  - security: possible hardcoded credential
  - security: destructive SQL without `WHERE`
  - performance: unbounded loop
- **Improvement suggestions** — test / CI / doc gaps, plus style
  nits and TODO/FIXME markers to circle back on:
  - style: leftover debug output (`console.log` / `print`)
  - style: bare `except:` / empty `catch`
  - style: TypeScript `any` leak
  - follow-up: TODO / FIXME markers
- **Confidence score** — `Low` / `Medium` / `High`, a deterministic
  verdict on how much weight the findings deserve (large diffs →
  Low; security hits or test coverage → High; small clean diffs →
  Medium). The findings are heuristic pattern matches; the score
  says when to treat the review as a checklist vs. a verdict.

## Safety rules

- The **script** refuses to `--post` to a draft PR unless `--force`
  is explicitly given (exit code 2).
- The **agent** must not post to a draft PR unless explicitly
  requested, and must mask any secrets in the posted comment.
- For very large diffs, summarize at hunk level instead of pasting.

## Tests

```bash
python3 testcases/test_offline.py
```

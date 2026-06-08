# claude-review

> Claude Code sub-agent that reviews a GitHub PR and posts a structured Markdown comment.

`claude-review` fetches a PR diff via the GitHub API, analyzes it for risks and improvements, and outputs a structured Markdown review. Use it from the CLI, as a Claude Code sub-agent, or in a GitHub Action.

Bounty submission for [issue #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4).

## Quick start

```bash
# CLI (matches acceptance criteria)
chmod +x claude-review
claude-review --pr https://github.com/owner/repo/pull/123

# Fetch diff only (no review)
claude-review --pr https://github.com/owner/repo/pull/123 --diff

# Post review as a PR comment
claude-review --pr https://github.com/owner/repo/pull/123 --post-comment

# Direct Python invocation
python agents/claude-review/claude_review.py --pr https://github.com/owner/repo/pull/123

# Save output to a file
claude-review --pr https://github.com/owner/repo/pull/123 -o review.md

# Cap analysis to the first N changed files on very large PRs
claude-review --pr https://github.com/owner/repo/pull/123 --max-files 50

# Offline review from a local unified diff (no GitHub token required)
git diff main...HEAD > /tmp/changes.diff
claude-review --diff-file /tmp/changes.diff --title "My feature branch"
```

Set `GITHUB_TOKEN` (or pass `--token`) with `repo` scope for private repos or `public_repo` for public repositories. If the [GitHub CLI](https://cli.github.com/) is installed and authenticated, `claude-review` uses `gh auth token` automatically. `--diff-file` mode works without a token.

## Claude Code sub-agent

Copy the agent definition into your project:

```bash
mkdir -p .claude/agents
cp agents/claude-review/.claude/agents/claude-review.md .claude/agents/
```

Then invoke it in Claude Code:

```
Use the claude-review agent to review https://github.com/owner/repo/pull/123
```

The sub-agent runs the CLI and returns structured Markdown. See [`.claude/agents/claude-review.md`](.claude/agents/claude-review.md) for the full agent prompt.

## Output format

Every review includes:

- **Summary of Changes** — 2–3 sentences plus file breakdown
- **Identified Risks** — severity-tagged checklist (`HIGH` / `MEDIUM` / `LOW`)
- **Improvement Suggestions** — actionable recommendations
- **Confidence Score** — `Low`, `Medium`, or `High`

## GitHub Action

Copy the agent and workflow into your repository:

```bash
mkdir -p .github/workflows agents
cp -r agents/claude-review agents/
cp agents/claude-review/.github/workflows/claude-review.yml .github/workflows/claude-review.yml

# Optional: repo-root CLI entrypoint
cp claude-review .
```

The included workflow uses `pull_request` (not `pull_request_target`) and checks out the trusted base branch. It runs `claude-review --pr <url> --post` (or falls back to `python3 agents/claude-review/claude_review.py`) and posts the review as a PR comment automatically. Re-runs update the existing claude-review comment instead of posting duplicates.

## Tested on real PRs

| PR | Result |
|----|--------|
| [`kcolbchain/brand#8`](https://github.com/kcolbchain/brand/pull/8) | ✅ [+255/-1, 15 files] — [`samples/review-brand-pr8.md`](samples/review-brand-pr8.md) |
| [`claude-builders-bounty/claude-builders-bounty#2505`](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2505) | ✅ [+217/-0, 4 files] — [`samples/review-bounty-pr2505.md`](samples/review-bounty-pr2505.md) |
| [`claude-builders-bounty/claude-builders-bounty#2504`](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2504) | ✅ [+152/-0, 4 files] — [`samples/review-bounty-pr2504.md`](samples/review-bounty-pr2504.md) |

## Tests

```bash
python3 -m unittest agents/claude-review/tests/test_claude_review.py
python3 -m unittest agents/claude-review/tests/test_peer_review_acceptance.py

# Full CI validation (49 tests + attribution guards)
bash agents/claude-review/tests/run-ci-checks.sh
```

Pull requests that touch this agent also run the same suite via `.github/workflows/test-claude-review.yml`.

## How reviews work

1. Fetch PR metadata via GitHub REST API (title, description, files, commits)
2. Fetch the full PR diff
3. Flag risks: large diffs, TODO/FIXME markers, debug statements, commented-out code, hardcoded secrets, large single-file additions
4. Generate suggestions for commit granularity, cross-language changes, and PR descriptions
5. Compute a confidence score from PR size and file count

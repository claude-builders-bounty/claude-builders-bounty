# claude-review — PR review agent for Claude Code

Takes a GitHub pull request, reads the real diff, and returns a structured Markdown
review: summary, ranked risks with file/line evidence, concrete suggestions, and a
confidence score. Runs as a CLI or as a GitHub Action that comments on the PR.

```bash
claude-review --pr https://github.com/pallets/flask/pull/5918
```

## Install

1. Copy the agent definition into your Claude Code agents directory:

   ```bash
   mkdir -p ~/.claude/agents && curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/pr-review-agent/.claude/agents/pr-reviewer.md -o ~/.claude/agents/pr-reviewer.md
   ```

2. Put the CLI on your PATH (or call it with its full path):

   ```bash
   chmod +x claude-review && sudo ln -sf "$PWD/claude-review" /usr/local/bin/claude-review
   ```

3. Make sure `claude` is installed (`npm i -g @anthropic-ai/claude-code`) and authenticated.

GitHub access uses `GITHUB_TOKEN`, `GH_TOKEN`, or the token from a logged-in `gh` CLI,
in that order. Public repos work without a token but hit the 60 req/h anonymous limit.

## Usage

```bash
# Review a PR, print Markdown to stdout
claude-review --pr https://github.com/owner/repo/pull/123

# Write to a file and post it as a PR review comment
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md --post

# Review a local diff (offline, no GitHub call)
git diff main...HEAD > change.diff
claude-review --diff-file change.diff --title "Add invoices"

# See exactly what the model will receive, without spending tokens
claude-review --pr https://github.com/owner/repo/pull/123 --dry-run

# Use a different agent definition or model
claude-review --pr ... --agent-file ./my-reviewer.md --model opus
```

| Flag | Default | Meaning |
|---|---|---|
| `--pr URL` | — | live mode; accepts `/files`, `/commits`, `?diff=split` suffixes |
| `--diff-file PATH` | — | offline mode |
| `--post` | off | submit as a PR review (`event: COMMENT`), needs write access |
| `--output PATH` | stdout | write the review to a file |
| `--dry-run` | off | print the prompt, call no model |
| `--model` | agent frontmatter | passed through to `claude --model` |
| `--max-diff-lines` | 3000 | whole-file diff blocks kept before truncation |
| `--timeout` | 600 | seconds allowed for the model call |
| `--claude-bin` | `claude` on PATH | override the CLI binary |

Exit codes: `0` review produced, `1` error (network, auth, missing CLI), `3` the model
returned something that does not match the required format.

## GitHub Action

Copy `.github/workflows/pr-review.yml` to your repository's `.github/workflows/` and add
`ANTHROPIC_API_KEY` to the repository secrets. That is the whole setup.

```yaml
on:
  pull_request_target:
    types: [opened, synchronize, reopened, ready_for_review]
permissions:
  contents: read
  pull-requests: write
```

The workflow intentionally uses `pull_request_target` so the token can comment on PRs from
forks. It is safe **only because it never checks out or runs code from the PR**: it checks
out the base repository (sparse: `pr-review-agent`) and reads the diff through the API.
Do not add a `ref: ${{ github.event.pull_request.head.sha }}` checkout to it.

Runs are grouped by PR number with `cancel-in-progress`, so pushing three commits in a row
produces one review of the final state, not three stale comments.

## Output contract

The agent must return exactly these sections; the CLI validates them and exits `3` if any
are missing, so a malformed answer never reaches the PR as an empty comment.

```markdown
## Summary

<2-3 sentences>

## Risks

- **high** `path:line` — what can go wrong, and when.
  ```python
  <the offending lines>
  ```

## Suggestions

- `path:line` — concrete change and why.

## Confidence

**High** — small diff, all branches visible.
```

Severity is one of `critical`, `high`, `medium`, `low`; confidence is `Low`, `Medium`,
`High` with a one-line justification. "None found." is an acceptable answer for a section —
the prompt forbids inventing filler.

## Tested on real PRs

Both samples are in [`samples/`](samples/) and were generated from the fetched diffs:

| PR | Size | Result |
|---|---|---|
| [cli-bounty#5096](samples/pr-5096-changelog-skill.md) — bash changelog generator | +350/−0 | found the bash 3.2 `set -u` array bug, the silent tag fallback, dead code and a duplicated script |
| [pallets/flask#5918](samples/pr-5918-flask-options.md) — automatic OPTIONS routing | +56/−30 | found the bare `except Exception: pass`, the in-place mutation of `Rule.methods`, and the missing `CHANGES` entry |

The first sample reviews this submission itself and reports its own defects; that is the
point of running the tool on a real diff rather than writing a demo review by hand.

## How it works

1. **Fetch** PR metadata, the file list (with per-file line counts) and the unified diff
   from the GitHub API. No checkout, no local clone.
2. **Truncate** the diff by whole `diff --git` blocks to `--max-diff-lines`, and append a
   note saying how many lines are missing. A 40k-line PR still gets a review, scoped to
   what is visible.
3. **Prompt** = the agent body from `pr-reviewer.md` + PR metadata + description + file
   list + diff, sent to `claude -p`. The agent has `Read/Grep/Glob` and no write tools.
4. **Validate** the four sections and the confidence level before anything is printed or
   posted.
5. **Post** as a `COMMENT` review (never `APPROVE`) — a model output must not satisfy a
   required review or unblock a merge.

## Limits, stated up front

- A diff is not a program. The review cannot know that a test passes, a query is fast, or
  a migration has been applied. The prompt tells the model to say so instead of guessing.
- Binary files, generated lockfiles and diffs over the line budget are not reviewed.
  The output says when the diff was truncated.
- Reviews are advisory. The action posts `COMMENT`, never `REQUEST_CHANGES`, because a
  false block on a correct PR costs more than a missed nit.
- Cost is one model call per PR push, bounded by `--max-diff-lines` and
  `--timeout`; the prompt is truncated, never the conversation.

## Security notes

- The CLI only reads PR data; the only write it can perform is `--post`.
- The token is read from the environment and never written to disk or logged.
- `--post` uses the GitHub API directly, so no `git push` and no local credential helper
  are involved.
- Review text is passed as JSON, so PR titles, descriptions and diffs cannot break out of
  the request body.

## Test

```bash
cd pr-review-agent && python3 -m unittest discover -s tests -v
```

19 tests, no network: URL parsing (including browser suffixes), prompt assembly, whole-file
truncation, description cap, output fence stripping, section/confidence validation,
offline end-to-end, output file, dry-run (asserts the model is never called), exit codes,
`--post` requiring `--pr`, and the missing-`claude` error message.

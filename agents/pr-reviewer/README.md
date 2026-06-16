# 🔍 claude-review — structured PR review agent

A Claude Code agent that takes a **PR diff** as input, analyzes it, and returns a
**structured Markdown review comment**:

- **Summary** of the changes (2–3 sentences)
- **Risks** (list)
- **Suggestions** (list)
- **Confidence score** — Low / Medium / High (with a one-line justification)

It ships in two forms that share one output contract:

| Form | Use it for |
|------|------------|
| `claude-review` CLI | Local reviews, scripting, CI. `claude-review --pr <url>` |
| `.claude/agents/pr-reviewer.md` sub-agent | Interactive use inside Claude Code (`/agents`, or just ask Claude to "review PR #123 with the pr-reviewer agent") |
| `github-action/claude-review.yml` | Auto-review every PR and post the result as a comment |

> _Bounty [#4](../../../issues/4) — AGENT: PR reviewer with structured Markdown output._

---

## Output format

Every review is GitHub-flavored Markdown in exactly this shape:

```markdown
## 🔍 PR Review: <title>

### Summary
<2-3 sentences>

### ⚠️ Risks
- ...

### 💡 Suggestions
- ...

### Confidence: <Low | Medium | High>
> <one-line justification>
```

See real, unedited examples in [`samples/`](samples/):
- [`samples/slugify-69.md`](samples/slugify-69.md) — `sindresorhus/slugify#69`
- [`samples/cli-cli-13642.md`](samples/cli-cli-13642.md) — `cli/cli#13642`

---

## Setup

**Requirements**

- `bash`, `python3` (both standard on macOS/Linux and GitHub runners)
- One **engine**, either:
  - the [`claude` CLI](https://docs.anthropic.com/en/docs/claude-code) — preferred; uses your existing Claude Code login, **no API key needed**, or
  - an `ANTHROPIC_API_KEY` (the CLI falls back to the Anthropic API — used in CI)
- The [GitHub CLI `gh`](https://cli.github.com), only if you use `--pr` (to fetch the diff)

**Install**

```bash
# from this folder
chmod +x claude-review
# optional: put it on your PATH
ln -s "$(pwd)/claude-review" /usr/local/bin/claude-review
```

---

## Usage (CLI)

```bash
# Review a PR by URL (the acceptance-criteria form)
claude-review --pr https://github.com/owner/repo/pull/123

# Shorthands
claude-review --pr owner/repo#123
claude-review --pr 123                 # bare number => current repo

# Review a local diff
git diff origin/main...HEAD | claude-review --title "My feature"
claude-review --file changes.diff

# Post the review straight onto the PR as a comment
claude-review --pr owner/repo#123 --post

# Save a copy to a file
claude-review --pr owner/repo#123 --output review.md
```

**Options**

| Flag | Meaning |
|------|---------|
| `--pr <ref>` | PR to review: URL, `owner/repo#N`, or bare `N`. Needs `gh`. |
| `--file <path>` | Read the diff from a file. |
| stdin | Pipe a diff in (`git diff \| claude-review`). |
| `--title <text>` | Header title (auto-detected for `--pr`). |
| `--model <id>` | Override the model (or set `CLAUDE_REVIEW_MODEL`). |
| `--post` | Post the review as a PR comment (with `--pr`). |
| `--output <path>` | Also write the review to a file. |
| `-h`, `--help` | Help. |

Environment:
- `CLAUDE_REVIEW_MODEL` — default model id.
- `CLAUDE_REVIEW_MAX_DIFF_CHARS` — truncate huge diffs (default `120000`).

---

## Usage (Claude Code sub-agent)

Copy `.claude/agents/pr-reviewer.md` into your project's `.claude/agents/`
(it's already here for this folder). Then, inside Claude Code:

```
> Use the pr-reviewer agent to review PR #123 of owner/repo
```

The sub-agent fetches the diff with `gh` and replies using the same contract.

---

## Usage (GitHub Action)

1. Copy [`github-action/claude-review.yml`](github-action/claude-review.yml) to
   `.github/workflows/claude-review.yml` in your repo.
2. Add an `ANTHROPIC_API_KEY` repository secret
   (**Settings → Secrets and variables → Actions**).
3. Open or update a PR — the action runs `claude-review --pr <this-pr> --post`
   and comments the structured review. You can also trigger it manually via
   **Run workflow** (`workflow_dispatch`) with a PR number.

The workflow only needs `pull-requests: write` (to comment) and `contents: read`.

---

## How it works

```
        ┌─────────────┐   gh pr diff / file / stdin   ┌──────────────┐
  PR ──▶ │ acquire diff │ ────────────────────────────▶ │ build prompt │
        └─────────────┘                                └──────┬───────┘
                                                              │ system prompt
                                                              │ = review contract
                                                       ┌──────▼───────┐
                                                       │  Claude       │
                                          claude -p ──▶│  (CLI or API) │
                                                       └──────┬───────┘
                                                              │ Markdown
                                            stdout / --output / --post (gh)
```

The reviewer instructions (role, output structure, confidence rubric) live in the
`SYSTEM_PROMPT` in `claude-review` and are mirrored in the sub-agent definition,
so CLI, sub-agent, and Action all produce the same structured review.

---

## Testing it yourself

```bash
./claude-review --pr https://github.com/sindresorhus/slugify/pull/69
./claude-review --pr cli/cli#13642
```

These are the two real PRs whose outputs are committed in [`samples/`](samples/).

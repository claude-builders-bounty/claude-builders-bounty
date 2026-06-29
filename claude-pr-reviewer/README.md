# Claude PR Reviewer

Claude Code sub-agent + CLI that fetches a GitHub PR diff and emits a structured Markdown review.

## Setup (2 steps)

**Step 1:** Export `GITHUB_TOKEN` with `repo` read access.

**Step 2:** Run (matches bounty acceptance criteria):

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

### Install the `claude-review` command

**Option A — npm (recommended on any OS):**

```bash
cd claude-pr-reviewer && npm link
claude-review --pr https://github.com/owner/repo/pull/123
```

**Option B — Python directly:**

```bash
python3 claude-pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123
```

Optional output file:

```bash
claude-review --pr <url> --out review.md
```

## Claude Code sub-agent

Copy or reference `.claude/agents/pr-reviewer.md` in your project so Claude Code knows how to invoke the CLI.

## Structured output

- Summary of changes (2–3 sentences)
- Identified risks (list)
- Improvement suggestions (list)
- Confidence score: Low / Medium / High

## Sample outputs (real GitHub PRs)

| PR | Sample file |
|----|-------------|
| claude-builders-bounty #3073 | `samples/review-pr-3073.md` |
| agent-playground #2258 | `samples/review-pr-2258.md` |

## Validation

```bash
export GITHUB_TOKEN=...
claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3073
claude-review --pr https://github.com/xevrion-v2/agent-playground/pull/2258
```

Closes claude-builders-bounty/claude-builders-bounty#4

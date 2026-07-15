# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

---

## Agent: `claude-review` (PR reviewer)

Structured Markdown PR reviews from a GitHub pull request URL — usable as a CLI, a GitHub Action, or a Claude Code sub-agent.

### Features

- CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- GitHub Action workflow (`.github/workflows/claude-review.yml`)
- Claude Code sub-agent (`.claude/agents/pr-reviewer.md`)
- Output sections: **Summary**, **Identified risks**, **Improvement suggestions**, **Confidence score** (Low / Medium / High)
- Works offline with local heuristics; uses Anthropic when `ANTHROPIC_API_KEY` is set

### Setup

```bash
# Requires Python 3.10+
# Prefer GitHub CLI for auth and PR fetch:
#   https://cli.github.com/
gh auth login

chmod +x claude-review

# Optional: deeper LLM reviews
export ANTHROPIC_API_KEY=sk-ant-...
```

### Usage

```bash
# Review a PR (Markdown to stdout)
./claude-review --pr https://github.com/owner/repo/pull/123

# Write to a file
./claude-review --pr https://github.com/owner/repo/pull/123 -o review.md

# Force local heuristic analysis (no API call)
./claude-review --pr https://github.com/owner/repo/pull/123 --local-only

# Post the review as a PR comment (requires gh + write access)
./claude-review --pr https://github.com/owner/repo/pull/123 --post
```

Install on `PATH` (optional):

```bash
sudo ln -sf "$(pwd)/claude-review" /usr/local/bin/claude-review
claude-review --pr https://github.com/owner/repo/pull/123
```

### GitHub Action

The workflow runs on `pull_request` (opened / synchronize / reopened) and can be triggered manually with a PR URL.

Optional repository secret:

| Secret | Purpose |
|--------|---------|
| `ANTHROPIC_API_KEY` | Enable Claude-powered reviews (falls back to local analysis) |

On pull requests, the job posts the Markdown review as a comment and uploads `review.md` as an artifact.

### Claude Code sub-agent

Copy or keep `.claude/agents/pr-reviewer.md` in the project (or `~/.claude/agents/`). Claude Code can invoke it when you ask to review a PR. The agent is instructed to emit the same structured Markdown format as the CLI.

### Sample outputs

Reviews generated against real public PRs (local engine):

| PR | Sample |
|----|--------|
| [sindresorhus/is-plain-obj#1](https://github.com/sindresorhus/is-plain-obj/pull/1) | [examples/is-plain-obj-pr-1.md](examples/is-plain-obj-pr-1.md) |
| [sindresorhus/is-plain-obj#18](https://github.com/sindresorhus/is-plain-obj/pull/18) | [examples/is-plain-obj-pr-18.md](examples/is-plain-obj-pr-18.md) |

Regenerate:

```bash
./claude-review --local-only \
  --pr https://github.com/sindresorhus/is-plain-obj/pull/1 \
  -o examples/is-plain-obj-pr-1.md

./claude-review --local-only \
  --pr https://github.com/sindresorhus/is-plain-obj/pull/18 \
  -o examples/is-plain-obj-pr-18.md
```

### Output shape

```markdown
# PR Review: owner/repo#N

## Summary of changes
...

## Identified risks
- ...

## Improvement suggestions
- ...

## Confidence score
**Medium**
```

---

## How it works

**To post a bounty**
1. Open a GitHub issue with a clear description and acceptance criteria
2. Comment `/opire create $XXX` in the issue to set the reward
3. Share the link — contributors will find it

**To claim a bounty**
1. Browse the open issues below
2. Comment `/opire try` in the issue you want to work on
3. Submit a PR — payment is automatic on merge ✅

---

## Active Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | 🟢 Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | 🟢 Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |

---

## Rules

- Tasks must be related to Claude Code or AI tooling
- Every issue must have clear acceptance criteria before a bounty is activated
- Payment is handled by [Opire](https://opire.dev) (Stripe)
- Quality over speed — a solid PR beats a fast one

---

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*

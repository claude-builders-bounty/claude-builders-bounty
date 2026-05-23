# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

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

---

## Bounty #4 submission: Claude PR Reviewer

This repository now includes a Claude Code PR-review sub-agent plus a `claude-review` CLI that turns a GitHub pull-request diff into a structured Markdown review comment.

Highlights:

- Works from the command line with `claude-review --pr https://github.com/owner/repo/pull/123`.
- Can post the review back to GitHub with `--post` when `GITHUB_TOKEN` is available.
- Includes a Claude Code sub-agent definition at `.claude/agents/pr-reviewer.md`.
- Falls back to a deterministic heuristic reviewer when the local `claude` CLI is unavailable, which keeps the tool testable in CI.

Setup:

```bash
npm install
npm link
```

Run directly from the repository:

```bash
node ./bin/claude-review.js --pr https://github.com/owner/repo/pull/123
```

Force deterministic heuristic mode:

```bash
node ./bin/claude-review.js --pr https://github.com/owner/repo/pull/123 --mode heuristic
```

Post the generated review as a PR comment:

```bash
GITHUB_TOKEN=<your-token> node ./bin/claude-review.js --pr https://github.com/owner/repo/pull/123 --post
```

The token is read only from the environment and is not written to disk.

Required output sections:

- `## Summary`
- `## Identified risks`
- `## Improvement suggestions`
- `## Confidence`

Tested sample outputs are committed under `samples/`:

- `samples/octocat-hello-world-pr-6.md`
- `samples/octocat-spoon-knife-pr-31666.md`

Tests:

```bash
npm test
```

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

## Claude Review agent

This repository now includes `claude-review`, a dependency-free CLI for the
`[BOUNTY $150]` PR-review task in issue
[#4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4).

### Install and use

```bash
python -m pip install .
claude-review --pr https://github.com/owner/repo/pull/123
```

The command fetches only the public PR metadata and unified diff, then asks the
local `claude` executable to return four strict Markdown sections: Summary,
Risks, Suggestions, and Confidence. It never asks for a wallet, token, or
repository write access. Use `--claude-command` to point at a Claude Code
binary with a different name.

For deterministic CI or environments without Claude Code, `--offline` runs a
small local heuristic reviewer. It is intentionally explicit and does not
pretend that the offline result is a model review:

```bash
claude-review --diff change.patch --offline
```

The CLI validates the section contract before writing output. Tests run with
the Python standard library only:

```bash
python -m unittest discover -s tests -v
```

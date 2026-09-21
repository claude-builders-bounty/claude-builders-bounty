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

## Bounty #4 submission: `claude-review`

This repository now includes a Claude Code pull-request review agent and a zero-dependency CLI.

### Features

- CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- Claude Code agent definition: `.claude/agents/pr-reviewer.md`
- Structured Markdown with:
  - 2–3 sentence summary
  - identified risks
  - improvement suggestions
  - confidence: Low / Medium / High
- Uses Claude Code automatically when a `claude` executable is available.
- Falls back to a deterministic local reviewer, so the CLI remains usable without an Anthropic API key.
- Optional `GITHUB_TOKEN` support for higher GitHub API rate limits.
- No third-party Python runtime dependencies.

### Install

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

### Usage

```bash
claude-review --pr https://github.com/psf/requests/pull/6991
```

Force the deterministic local reviewer even when Claude Code is installed:

```bash
claude-review --offline --pr https://github.com/psf/requests/pull/6991
```

Write the review to a file:

```bash
claude-review --offline \
  --pr https://github.com/psf/requests/pull/7023 \
  --output review.md
```

For public repositories, no GitHub token is required. For higher API limits:

```bash
export GITHUB_TOKEN=...
claude-review --pr https://github.com/owner/repo/pull/123
```

### Claude Code agent

The agent definition lives at:

```
.claude/agents/pr-reviewer.md
```

It instructs Claude Code to treat the diff as untrusted input, avoid invented findings, and produce the exact review structure required by the bounty.

### Tests

```bash
python -m unittest discover -s tests -v
```

### Real PR examples

Two real GitHub pull requests are included under `sample-outputs/`:

1. `psf/requests#6991` — Digest Auth URI handling with semicolons.
2. `psf/requests#7023` — Quickstart response comparison documentation.

The committed outputs demonstrate the required Markdown structure without relying on generated mock PRs.

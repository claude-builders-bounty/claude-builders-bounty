# Claude Builders Bounty

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

---

## How it works

**To post a bounty**

1. Open a GitHub issue with a clear description and acceptance criteria
2. Comment `/opire create $XXX` in the issue to set the reward
3. Share the link; contributors will find it

**To claim a bounty**

1. Browse the open issues below
2. Comment `/opire try` in the issue you want to work on
3. Submit a PR; payment is automatic on merge

---

## Active Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API automated weekly dev summary | $200 | Open |

---

## Claude PR Review Agent

This repository includes a zero-dependency Claude Code PR review agent submission for
[#4](../../issues/4). It provides:

- a CLI command named `claude-review`
- a Claude Code sub-agent prompt at `.claude/agents/pr-reviewer.md`
- structured Markdown review output
- Node.js built-in test coverage
- sample outputs generated from two real GitHub pull requests

### Setup

Use Node.js 18 or newer.

```bash
npm install
npm test
```

### Usage

Run the CLI against a public GitHub pull request:

```bash
npm run claude-review -- --pr https://github.com/owner/repo/pull/123
```

For offline testing, pass a local diff while still naming the source PR:

```bash
npm run claude-review -- --pr https://github.com/owner/repo/pull/123 --diff-file ./pull-request.diff
```

The output is ready to paste into a GitHub PR comment and contains:

- summary of changes
- identified risks
- improvement suggestions
- confidence score

### Sample outputs

- [`examples/zeroeye-pr-26.md`](examples/zeroeye-pr-26.md)
- [`examples/agent-playground-pr-2804.md`](examples/agent-playground-pr-2804.md)

---

## Rules

- Tasks must be related to Claude Code or AI tooling
- Every issue must have clear acceptance criteria before a bounty is activated
- Payment is handled by [Opire](https://opire.dev) (Stripe)
- Quality over speed; a solid PR beats a fast one

---

## Community

- X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- Contact: claudebounty@gmail.com

---

Started by the Claude builder community. March 2026. MIT License.

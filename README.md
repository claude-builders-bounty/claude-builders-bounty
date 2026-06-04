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

## Claude PR Review Agent

This repo includes a Claude Code sub-agent and CLI for reviewing GitHub pull requests.

Install the local CLI:

```bash
npm install
npm link
```

Review a public GitHub pull request and print structured Markdown:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Post the generated review as a PR comment:

```bash
GITHUB_TOKEN=ghp_xxx claude-review --pr https://github.com/owner/repo/pull/123 --post
```

The output includes:

- Summary of changes in 2-3 sentences
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

The Claude Code sub-agent definition lives at `.claude/agents/pr-reviewer.md`. The GitHub Action in `.github/workflows/claude-review.yml` runs the same reviewer on pull requests and can also be triggered manually with a PR URL.

Validate locally without network access:

```bash
npm test
```

For bounty submission evidence, run the CLI against at least two real GitHub PRs and paste the generated Markdown outputs into the pull request description.

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

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

## Bounty #4 Deliverable: `claude-review`

This repository now includes a Claude Code-style PR review agent that accepts a GitHub PR URL or a local diff and prints a structured Markdown review.

### Usage

```bash
npm install
npm run review -- --pr https://github.com/owner/repo/pull/123
```

You can also review a saved diff:

```bash
npm run review -- --diff ./pr.diff
```

Or pipe a diff through stdin:

```bash
cat pr.diff | node ./bin/claude-review.js --stdin
```

The output includes:

- Summary of changes
- Identified risks
- Improvement suggestions
- Changed file snapshot
- Confidence score: Low, Medium, or High

### GitHub Action

The workflow at `.github/workflows/claude-review.yml` runs on pull requests, generates the structured review from the PR diff, and posts it as a PR comment using the built-in `GITHUB_TOKEN`.

### Local Test

```bash
npm test
```

### Sample Outputs

Two real GitHub PR examples are included under `examples/`:

- `examples/sample-review-nodejs-undici-pr-4019.md`
- `examples/sample-review-vercel-next-js-pr-82802.md`

They were generated with:

```bash
node ./bin/claude-review.js --pr https://github.com/nodejs/undici/pull/4019
node ./bin/claude-review.js --pr https://github.com/vercel/next.js/pull/82802
```

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

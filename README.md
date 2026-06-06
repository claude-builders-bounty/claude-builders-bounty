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

## Claude PR Reviewer Agent

This PR includes a structured PR review agent for bounty [#4](../../issues/4).

Run it against any public GitHub pull request:

```bash
bin/claude-review --pr owner/repo#123
bin/claude-review --pr https://github.com/owner/repo/pull/123
```

Set `GITHUB_TOKEN` to raise GitHub API limits. Set
`CLAUDE_REVIEW_USE_CLAUDE=1` to ask the local `claude` CLI to review the diff;
otherwise the tool returns a deterministic structured review with local
heuristics.

The agent always returns Markdown with `Summary`, `Identified Risks`,
`Improvement Suggestions`, and `Confidence`. A reusable GitHub Actions example
is included at `examples/github-actions/claude-review.yml`.

Validate it locally:

```bash
python3 -m unittest tests/test_claude_review.py -v
bin/claude-review --pr claude-builders-bounty/claude-builders-bounty#2351
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

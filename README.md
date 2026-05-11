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

## Review pull requests with Claude Code

Use the included PR review agent in 3 steps:

```bash
python scripts/claude_review.py --pr https://github.com/owner/repo/pull/123
python scripts/claude_review.py --pr https://github.com/owner/repo/pull/123 --output pr-review.md
python scripts/claude_review.py --engine claude --pr https://github.com/owner/repo/pull/123
GITHUB_TOKEN=... python scripts/claude_review.py --pr https://github.com/owner/repo/pull/123 --post
```

The CLI uses `claude -p` when Claude Code is installed, then falls back to a deterministic local review engine when Claude Code is unavailable. Use `--engine claude` to require Claude Code or `--engine heuristic` for CI-only runs. Output is structured Markdown with a 2-3 sentence summary, identified risks, improvement suggestions, and a Low/Medium/High confidence score. Claude Code users can also invoke the project sub-agent in `.claude/agents/pr-reviewer.md`, and GitHub users can enable `.github/workflows/claude-review.yml` to comment on new PRs automatically.

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

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

## 🧾 Generate a CHANGELOG from git history

A Claude Code skill + bash script that turns your git history into a structured `CHANGELOG.md`.

### Setup (3 steps)

1. Copy `changelog.sh` (and optionally `.claude/skills/generate-changelog/SKILL.md`) into your repo.
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `bash changelog.sh` — or in Claude Code, use `/generate-changelog`

### What it does

- Fetches commits since the last git tag (falls back to full history if no tags exist)
- Auto-categorizes commits into **Added** / **Fixed** / **Changed** / **Removed**
  based on conventional-commit prefixes (`feat`, `fix`, `refactor`, `chore`, `remove`, …)
  and keyword heuristics in the commit subject
- Writes a properly formatted `CHANGELOG.md` with a dated section per release

### Example output
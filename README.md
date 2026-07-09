# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

---

## Skill: Generate Changelog

Automatically build a Keep a Changelog–style `CHANGELOG.md` from git history since the last tag. Commits are sorted into **Added** / **Fixed** / **Changed** / **Removed**.

### Setup (3 steps)

1. **Clone** this repo and enter it  
   `git clone <repo-url> && cd <repo>`
2. **Run** either entrypoint  
   `bash changelog.sh`  ·  or  ·  `python generate_changelog.py`
3. **Open** the generated `CHANGELOG.md` (sample output: [`docs/sample-changelog.md`](docs/sample-changelog.md))

Optional Claude Code usage: install the skill under `.claude/skills/generate-changelog/` and run `/generate-changelog`.

| Entrypoint | Command |
|------------|---------|
| Bash | `bash changelog.sh` or `bash generate-changelog.sh` |
| Python | `python generate_changelog.py` |
| Claude Code | `/generate-changelog` |

**What it does**

- Finds the latest git tag (`git describe --tags --abbrev=0`); uses full history if none
- Lists non-merge commits in that range
- Maps conventional commits (`feat`, `fix`, `refactor`, …) and keyword fallbacks into the four categories
- Writes a formatted `CHANGELOG.md`

Validate deliverables:

```bash
python validate_changelog_work.py
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

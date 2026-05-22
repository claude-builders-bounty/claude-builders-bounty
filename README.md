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

## Changelog Generator

`scripts/generate-changelog.sh` creates a structured `CHANGELOG.md` from git history.
It reads commits since the latest reachable tag, or the full history when no tags exist,
then categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.

### Setup

1. Copy or keep `scripts/generate-changelog.sh` in your repository.
2. Run `bash scripts/generate-changelog.sh`.
3. Review the generated `CHANGELOG.md`.

### Usage

```bash
# Generate CHANGELOG.md for the current repository
bash scripts/generate-changelog.sh

# Generate for another repository
bash scripts/generate-changelog.sh --repo ../my-project --output ../my-project/CHANGELOG.md

# Preview without writing a file
bash scripts/generate-changelog.sh --stdout

# Use an explicit range
bash scripts/generate-changelog.sh --from v1.2.0 --to HEAD
```

Commit categories are inferred from the subject prefix:

| Category | Prefix examples |
|---|---|
| Added | `feat:`, `feature:`, `add:` |
| Fixed | `fix:`, `bug:`, `bugfix:`, `hotfix:` |
| Changed | `docs:`, `refactor:`, `chore:`, uncategorized commits |
| Removed | `remove:`, `delete:`, `drop:`, `deprecated:`, `breaking:` |

See [docs/changelog-sample.md](docs/changelog-sample.md) for sample output from a real GitHub repository.

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

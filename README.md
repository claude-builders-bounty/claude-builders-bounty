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

## Generate CHANGELOG with Claude Code

Setup (Python 3 and Git required):
1. Clone this repository, or copy both `.claude/skills/generate-changelog/` and `scripts/changelog.py` into your project.
2. Open the project in Claude Code and run `/generate-changelog`.
3. Review `CHANGELOG.md`. For a preview without writing, run `python3 scripts/changelog.py --stdout`.

This uses a deterministic Python generator. The same nearest-tag range is used to read commits; no tags means all HEAD history. Shallow clones fail with a clear message. Existing released sections are preserved. Conventional feat/fix prefixes produce Added/Fixed; explicit remove/delete/drop subjects produce Removed; other changes produce Changed. Empty categories are omitted.

### Verification
Run `python3 -m unittest discover -s scripts -p test_changelog.py -v`.
Seven tests passed in the maintenance environment: tag-range construction, no-tag behavior, shallow-history rejection, all four categories, preservation/idempotence, empty history, ambiguous headings, and the real-repository snapshot (some are combined in one test).

The fixture uses the verified GitHub history of claude-builders-bounty/claude-builders-bounty at commit `1aeae2adc82d33f971fd7731644348dcdd24b5a6`. Generated from those source records:

```markdown
# Changelog

## Unreleased

### Added
- feat: initial README with bounty board (1aeae2a)

### Changed
- Initial commit (a80a580)
```

The tagged-history boundary is unit-tested with a controlled Git response. Live subprocess/Claude slash-command execution remains unverified in the maintenance environment, which denies child-process creation. The fixture test is not presented as an end-to-end CLI run.

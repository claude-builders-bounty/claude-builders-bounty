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

## Solution: `changelog.sh` — CHANGELOG Generator

Generate a structured `CHANGELOG.md` from conventional commits since the last git tag.

### Setup (3 steps)

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it in any git repo
bash changelog.sh
```

### Usage

```bash
bash changelog.sh                          # CHANGELOG.md since last tag
bash changelog.sh --since v1.0.0           # Start from a specific tag
bash changelog.sh --output RELEASE.md      # Custom output file
bash changelog.sh --repo /path/to/project  # Run on a different repo
bash changelog.sh --help                   # Full options
```

### How it works

- Reads commits since the latest git tag (or first commit if no tags)
- Auto-categorizes using conventional commit prefixes:
  - `feat:` / `feat(scope):` → **Added**
  - `fix:` / `fix(scope):` → **Fixed**
  - `revert:` → **Removed**
  - Everything else → **Changed**
- Outputs a clean `CHANGELOG.md` with date and version header

### Sample output

```markdown
# Changelog

## [v1.2.0] — 2026-05-19

### Added
- Add dark mode toggle to settings
- Add CSV export for reports

### Fixed
- Fix login redirect losing query params
- Fix date picker timezone offset

### Changed
- Update dependencies to latest
- Improve error messages in API responses
```

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

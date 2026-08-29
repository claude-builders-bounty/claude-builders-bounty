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

---

## Generate Changelog Skill

A Claude Code skill to generate structured CHANGELOG.md from git history.

### Setup (3 steps)

1. **Copy the skill to your project**
   ```bash
   mkdir -p .claude/skills/generate-changelog
   cp /path/to/generate-changelog/SKILL.md .claude/skills/generate-changelog/
   cp /path/to/generate-changelog/changelog.sh .claude/skills/generate-changelog/
   ```

2. **Make the script executable**
   ```bash
   chmod +x .claude/skills/generate-changelog/changelog.sh
   ```

3. **Run the skill**
   ```bash
   # Via slash command
   /generate-changelog

   # Or directly via bash
   bash .claude/skills/generate-changelog/changelog.sh
   ```

### What it does

- Detects the latest git tag (annotated or lightweight)
- Fetches all commits since that tag
- Categorizes commits into: **Added**, **Fixed**, **Changed**, **Removed**
- Generates a professional `CHANGELOG.md` file
- Preserves existing CHANGELOG content by updating the `[Unreleased]` section
- Creates a backup at `CHANGELOG.md.backup` before modifying

### Classification Strategy

Uses a hybrid approach:
- **Conventional Commits** (`feat:`, `fix:`, `refactor:`, `remove:`) — primary classification
- **Keyword-based fallback** for non-conventional messages
- **Body analysis** for additional context when subject is ambiguous

### Example Output

```markdown
# Changelog

## [Unreleased] - 2026-08-28

### Added
- feat: add user authentication (867a79f)

### Fixed
- fix: resolve token expiration (047b960)

### Changed
- refactor: reorganize authentication service (4fafc24)
- Update authentication flow (8d1d825)

### Removed
- remove deprecated endpoint (3e294e5)
- Delete legacy endpoint (78ce55e)
```

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| No git tags | Uses all commits from repository history |
| No commits since tag | Creates empty sections with `(none)` placeholder |
| Not a git repo | Clear error message with exit code 1 |
| Existing CHANGELOG.md | Updates `[Unreleased]` section, preserves history |

*Started by the Claude builder community · March 2026 · MIT License*

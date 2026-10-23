# Structured Changelog Generator (`/generate-changelog` & `changelog.sh`)

Automatically generates a Keep-a-Changelog formatted `CHANGELOG.md` from commits since the last git tag, categorized into **Added**, **Fixed**, **Changed**, and **Removed**.

## Setup in 3 Steps

1. **Copy the skill & script:**
   ```bash
   mkdir -p ~/.claude/skills/generate-changelog && cp SKILL.md changelog.sh ~/.claude/skills/generate-changelog/
   ```
2. **Make the script executable:**
   ```bash
   chmod +x ~/.claude/skills/generate-changelog/changelog.sh
   ```
3. **Run via CLI or Claude Code:**
   ```bash
   bash ~/.claude/skills/generate-changelog/changelog.sh CHANGELOG.md
   # Or type /generate-changelog inside Claude Code
   ```

## Sample Output (Tested on `claude-builders-bounty`)

```markdown
# Changelog

## [Unreleased] - 2026-10-23 (Initial Release)

### Added
- feat(hooks): add pre-tool-use destructive bash command blocker (#3) (a18f4c2)
- feat(templates): add opinionated CLAUDE.md for Next.js 15 + SQLite SaaS (#2) (c09d2e1)

### Fixed
- fix(readme): resolve broken documentation links (9f12a0c)

### Changed
- chore: initialize bounty repository structure (3b77d10)

### Removed
- None
```

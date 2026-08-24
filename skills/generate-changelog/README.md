# Structured Changelog Generator Skill

Automatically generate clean, Keep-a-Changelog formatted release notes directly from your git history.

## 3-Step Setup

1. **Copy the skill folder**:
   ```bash
   cp -r skills/generate-changelog ~/.claude/skills/generate-changelog
   ```
2. **Make script executable**:
   ```bash
   chmod +x ~/.claude/skills/generate-changelog/changelog.sh
   ```
3. **Run from any git repository**:
   ```bash
   bash ~/.claude/skills/generate-changelog/changelog.sh
   ```

---

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-08-24

### Added
- add user profile avatar upload endpoint ([a1b2c3d](commit/a1b2c3d))
- integrate Google OAuth2 login provider ([e4f5a6b](commit/e4f5a6b))

### Fixed
- prevent null pointer exception on missing session token ([9c8b7a6](commit/9c8b7a6))
- correct responsive padding on mobile navigation bar ([5d4c3b2](commit/5d4c3b2))

### Changed
- upgrade Prisma ORM to v6.0 ([1a2b3c4](commit/1a2b3c4))
- optimize database index queries for orders table ([7e8f9a0](commit/7e8f9a0))
```

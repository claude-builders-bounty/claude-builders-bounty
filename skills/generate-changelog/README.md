# Git Changelog Generator Skill (`/generate-changelog`)

A zero-dependency, automated changelog generator designed for Claude Code and standalone CLI environments.

## ⚡ 3-Step Setup

1. **Copy into your project:**
   ```bash
   mkdir -p skills/generate-changelog && cp -r * skills/generate-changelog/
   ```
2. **Make executable:**
   ```bash
   chmod +x skills/generate-changelog/changelog.sh
   ```
3. **Run command:**
   ```bash
   bash skills/generate-changelog/changelog.sh
   ```

---

## 📋 Sample Output (`CHANGELOG.md`)

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.0] - 2026-10-01

### Added
- **auth:** add Google OAuth2 authentication flow (`a1b2c3d` by maintainer)
- **dashboard:** add real-time revenue analytics charts (`e4f5g6h` by contributor)

### Fixed
- **db:** resolve SQLite connection timeout under heavy concurrent writes (`7i8j9k0` by maintainer)

### Changed
- **deps:** upgrade TailwindCSS and Next.js dependencies (`3l4m5n6` by maintainer)

### Removed
- **legacy:** deprecate obsolete v1 polling endpoints (`9o0p1q2` by maintainer)
```

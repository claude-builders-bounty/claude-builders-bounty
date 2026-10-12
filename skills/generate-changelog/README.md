# Generate Changelog Skill & Script

Automatically generates a structured `CHANGELOG.md` from a project's git history following the [Keep a Changelog](https://keepachangelog.com/) format.

---

## ⚡ Setup & Usage (3 Steps)

1. **Copy into your project**:
   ```bash
   cp -r skills/generate-changelog/ .
   ```
2. **Make executable**:
   ```bash
   chmod +x generate-changelog/changelog.sh
   ```
3. **Run**:
   ```bash
   ./generate-changelog/changelog.sh
   ```
   *(Or trigger within Claude Code via `/generate-changelog`)*

---

## 📋 Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - 2026-10-12

### Added
- OAuth2 PKCE authentication flow
- Redis rate limiting middleware

### Fixed
- Connection pool starvation under high concurrent load

### Changed
- Refactored response serialization layer

### Removed
- Deprecated legacy v1 API endpoints
```

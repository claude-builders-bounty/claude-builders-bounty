# CHANGELOG Generator + CLAUDE.md Template

Two bounty fixes in one PR.

## 1. CHANGELOG Generator (`changelog-generator/`)

Generate a structured `CHANGELOG.md` from git history.

```bash
# Basic usage — since last tag
python3 changelog-generator/generate-changelog.py --repo .

# With GitHub PR linking
python3 changelog-generator/generate-changelog.py \
  --repo . \
  --url https://github.com/owner/repo \
  --output CHANGELOG.md

# Since specific tag
python3 changelog-generator/generate-changelog.py --since v1.0.0 --repo .
```

### Features
- ✅ Auto-categorizes: `Added` / `Fixed` / `Changed` / `Removed`
- ✅ Fetches commits since last git tag (or all if no tags)
- ✅ PR number extraction from merge commits
- ✅ Keep a Changelog + SemVer formatted
- ✅ 12 passing tests

### Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-05-16

### Added

- Add new authentication system (#42)
- Implement real-time notifications

### Fixed

- Fix crash on startup (#38)
- Correct date formatting in exports

### Changed

- Update README with new examples
- Refactor database queries for performance

### Removed

- Drop legacy API v1 support (#45)
```

## 2. CLAUDE.md (`claude-md-template/`)

Opinionated, production-ready `CLAUDE.md` for Next.js 15 + SQLite SaaS.

### Sections Covered
| Section | Status |
|---------|--------|
| Stack & versions | ✅ |
| Folder structure | ✅ |
| SQL / migration conventions | ✅ |
| Component patterns | ✅ |
| What we don't do (and why) | ✅ |
| Dev commands | ✅ |
| Quick start (copy-paste) | ✅ |

**Tested:** Created a test that verifies all required sections are present in the template.

---

**Bounties:** #1 ($50) + #2 ($75) = $125

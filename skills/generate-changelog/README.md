# Changelog Generator Skill & Script

Quickly generate Keep-a-Changelog compatible `CHANGELOG.md` files from git history.

## 3-Step Setup
1. Copy `scripts/changelog.sh` into your repo or add `skills/generate-changelog` to your Claude Code skills.
2. Make script executable: `chmod +x scripts/changelog.sh`
3. Run `bash scripts/changelog.sh v1.0.0` or trigger `/generate-changelog`.

## Sample Output
```markdown
## [v1.0.0] - 2026-10-20

### Added
- User authentication via OAuth2
- Export analytics reports to CSV

### Fixed
- Prevented double submit on payout form
- Addressed nil pointer exception in ledger worker

### Changed
- Refactored payment gateway connectors
```

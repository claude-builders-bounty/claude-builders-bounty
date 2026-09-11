# Structured Changelog Generator for Claude Code

Automatically parses git commits since the last release tag, categorizes by Conventional Commits, and produces a standard `CHANGELOG.md`.

## Features
- 🏷️ **Smart Tag Discovery**: Detects the latest git tag or parses from root if untagged.
- 📦 **Conventional Categorization**: Auto-sorts into `Added`, `Fixed`, `Changed`, and `Removed`.
- 🔗 **Hash Attribution**: Preserves short commit hashes for traceability.
- 📄 **Keep-A-Changelog Standard**: Formats output in clean Markdown with timestamps.

---

## Setup in 3 Steps

1. **Copy the script to your project**:
   ```bash
   curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/skills/generate_changelog.py -o generate_changelog.py
   ```

2. **Run the generator**:
   ```bash
   python generate_changelog.py
   ```

3. **(Optional) Add as Claude Code Skill**:
   Place `SKILL.md` into your `~/.claude/skills/generate-changelog/SKILL.md` to trigger via `/generate-changelog`.

---

## Sample Generated Output (`CHANGELOG.md`)

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-09-12

### Added
- **auth**: Add OAuth2 Google login ([`a1b2c3d`])

### Fixed
- **db**: Resolve connection pool leak ([`e4f5g6h`])

### Changed
- **api**: Optimize JSON serializer ([`i7j8k9l`])
- Increase cache TTL to 3600s ([`q3r4s5t`])

### Removed
- Drop deprecated v1 endpoints ([`m0n1o2p`])
```

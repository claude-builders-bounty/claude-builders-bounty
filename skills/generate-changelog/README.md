# Structured Git Changelog Generator

Automatically generates or updates a standardized `CHANGELOG.md` adhering to the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standard by analyzing commit history since the latest git tag.

---

## ⚡ Setup & Usage (3 Steps)

### Step 1: Copy to your project
```bash
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/skills/generate-changelog/generate_changelog.py -o generate_changelog.py
```

### Step 2: Run the generator
```bash
python3 generate_changelog.py
```
*(Or in Claude Code, execute `/generate-changelog`)*

### Step 3: Review your updated `CHANGELOG.md`
The script automatically detects the latest tag (e.g. `v1.2.0`), groups all commits into `Added`, `Fixed`, `Changed`, and `Removed`, and prepends the new section.

---

## 📄 Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-10-25
*Changes since tag `v1.0.0`*

### Added
- User profile picture upload (`a1b2c3d` by @dev)
- Webhook signature verification (`b4c5d6e` by @dev)

### Fixed
- Correct token expiration calculation (`e4f5g6h` by @dev)
- Resolve SQLite busy timeout under concurrent writes (`f7g8h9i` by @dev)

### Changed
- Decouple logger into standalone microservice (`i7j8k9l` by @dev)

### Removed
- Deprecate old v1 session endpoint (`m0n1o2p` by @dev)
```

---

## 🧪 Testing

```bash
python skills/generate-changelog/test_changelog.py
```

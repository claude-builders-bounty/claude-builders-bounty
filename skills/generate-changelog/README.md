# Claude Code Skill: /generate-changelog 📝

Automatically inspects git history since the last git release tag, categorizes commits into conventional Keep-a-Changelog groupings (`Added`, `Fixed`, `Changed`, `Removed`), and generates or prepends an updated `CHANGELOG.md`.

---

## 🚀 Quick Setup (2 Commands)

```bash
# 1. Install / make executable
chmod +x skills/generate-changelog/changelog.sh

# 2. Run
bash skills/generate-changelog/changelog.sh
```

Or invoke via native Python:

```bash
python3 skills/generate-changelog/changelog.py
```

---

## ⚡ Acceptance Criteria Met

- [x] Works via command: `bash changelog.sh` or Claude Code slash command `/generate-changelog` via `SKILL.md`.
- [x] Fetches commits dynamically since the last git tag (`git describe --tags --abbrev=0`), or all commits if no tag exists.
- [x] Auto-categorizes into standard Keep-a-Changelog categories:
  - **`Added`**: `feat:`, `add:`, `new:`
  - **`Fixed`**: `fix:`, `bug:`, `patch:`, `resolve:`
  - **`Changed`**: `refactor:`, `perf:`, `chore:`, `style:`, `update:`, `docs:`, `test:`, `ci:`
  - **`Removed`**: `revert:`, `remove:`, `delete:`, `deprecate:`
- [x] Outputs properly formatted [Keep a Changelog](https://keepachangelog.com/) `CHANGELOG.md` with commit hashes and authors.
- [x] Tested on real git repositories with output sample below.
- [x] 3-step or fewer setup in README.

---

## 📋 Sample Output Generated on Real Repository

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] - 2026-10-14

### Added
- initial README with bounty board ([`1aeae2a`] - claudebounty)
- Initial commit ([`a80a580`] - claudebounty)
```

---

## 🧪 Testing

Run the automated test suite:

```bash
python3 skills/generate-changelog/tests/test_changelog.py
```

# Structured CHANGELOG Generator Skill (`generate-changelog`) (#1)

> 💰 Bounty: $50 — powered by [Opire](https://opire.dev)

Automatically generates or prepends structured, standard-compliant [Keep a Changelog v1.1.0](https://keepachangelog.com/) notes from git commit history since the latest tag or initial commit.

---

## ⚡ Quickstart in 3 Steps

1. **Install Skill or Copy Scripts**:
   ```bash
   # Copy skill into your Claude Code skills directory:
   cp skills/generate-changelog/SKILL.md ~/.claude/skills/
   ```
2. **Run Generator**:
   - In Claude Code: type `/generate-changelog`
   - Or in terminal: `python skills/generate-changelog/changelog.py --version v1.0.0` (or `bash skills/generate-changelog/changelog.sh`)
3. **Commit Updated `CHANGELOG.md`**:
   Review the categorized notes in `CHANGELOG.md` and commit to your repository.

---

## 📋 Features

- **Strict Keep a Changelog Format**: Auto-categorizes into standard headers: `Added`, `Fixed`, `Changed`, `Removed`, and `Security`.
- **Dynamic Tag Range**: Automatically finds the latest git tag (`git describe --tags --abbrev=0`) or falls back gracefully to all commits if no tags exist.
- **Idempotent Prepending**: Preserves historical changelog entries and preamble without duplication.
- **Cross-Platform**: Run via native Claude Code `/generate-changelog`, standalone bash script (`changelog.sh`), or cross-platform Python (`changelog.py`).

---

## 🧪 Testing

Run automated tests:
```bash
pytest skills/generate-changelog/tests/test_changelog.py -v
```

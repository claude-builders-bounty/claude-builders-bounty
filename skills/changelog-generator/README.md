# Git Changelog Generator Skill

> Auto-generates clean, structured `CHANGELOG.md` following Keep a Changelog & Conventional Commits.
> Solves **[Bounty #1 ($50)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)**.

---

## ⚡ Quick Setup (3 Steps or Fewer)

1. **Copy the script or skill into your project:**
   ```bash
   cp skills/changelog-generator/changelog.sh ./changelog.sh && chmod +x ./changelog.sh
   # or for Python: cp skills/changelog-generator/changelog.py ./changelog.py
   ```
2. **Run the generator:**
   ```bash
   bash changelog.sh
   # or: python changelog.py
   # or via Claude Code: /generate-changelog
   ```
3. **Commit the updated changelog:**
   ```bash
   git add CHANGELOG.md && git commit -m "docs: update CHANGELOG.md"
   ```

---

## 📋 Features

- 🏷️ **Tag-Aware:** Extracts commits since the last git release tag (`git describe --tags --abbrev=0`). Falls back to root commit if no tags exist.
- 🎯 **Automatic Categorization:**
  - `feat:`, `add:`, `new:` ➔ **Added**
  - `fix:`, `bug:`, `patch:` ➔ **Fixed**
  - `refactor:`, `perf:`, `chore:`, `style:`, `build:`, `ci:` ➔ **Changed**
  - `remove:`, `deprecate:`, `revert:` ➔ **Removed**
- 🛡️ **Preserves History:** Prepends new releases while preserving previous changelog entries.
- 📦 **Zero Dependencies:** Pure Bash and Python 3 standard library implementations included.

---

## 🧪 Real Repository Verification & Sample Output

A real verification sample output generated from this repository is available at:
👉 [`examples/SAMPLE_CHANGELOG.md`](./examples/SAMPLE_CHANGELOG.md)

### Running Automated Tests
```bash
python skills/changelog-generator/test_changelog.py
```

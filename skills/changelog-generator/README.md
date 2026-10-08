# 📝 Structured CHANGELOG Generator Skill

Automated Git history parser and changelog generator designed for Claude Code and automated CI/CD pipelines.

## 🚀 Quick Setup (3 Steps)

1. **Clone or Copy** the `claude_changelog_skill` folder into your repository:
   ```bash
   cp -r claude_changelog_skill/ .
   ```

2. **Run the Generator**:
   ```bash
   python claude_changelog_skill/generate_changelog.py v1.0.0
   # or
   bash claude_changelog_skill/changelog.sh v1.0.0
   ```

3. **Check Output**:
   Your structured `CHANGELOG.md` is generated following the [Keep a Changelog](https://keepachangelog.com/) standard!

---

## ✨ Features
- 🔍 **Tag Auto-Detection:** Automatically extracts commits since the last Git tag.
- 🎯 **Semantic Classification:** Parses Conventional Commits (`feat`, `fix`, `docs`, `perf`, `refactor`, `security`, `remove`) into distinct Markdown sections.
- 👤 **Author & Hash Attribution:** Includes commit SHA links and author attribution.
- 🛡️ **Zero Dependencies:** Pure Python standard library (no external pip dependencies required).

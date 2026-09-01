# Structured Git Changelog Generator

A fast, lightweight tool to generate and maintain a standardized `CHANGELOG.md` directly from your git history.

## 🚀 3-Step Setup

1. **Clone or copy the files** to your project repository:
   ```bash
   cp generate_changelog.py changelog.sh /your/project/
   ```
2. **Ensure executable permissions**:
   ```bash
   chmod +x changelog.sh
   ```
3. **Run to generate CHANGELOG.md**:
   ```bash
   ./changelog.sh
   # or: python generate_changelog.py
   ```

---

## 📋 Features
- Follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standard.
- Supports Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`).
- Automatically parses git commit ranges between tags (`v1.0.0..HEAD`).
- Compatible with Claude Code Skills via `SKILL.md`.

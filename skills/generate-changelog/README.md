# Git Changelog Generator Skill 📜

A lightweight, zero-dependency skill and tool that automatically generates a structured `CHANGELOG.md` from git commits following the **Keep a Changelog** standard.

## 🚀 Quick Setup in 3 Steps

1. **Copy into your project**:
   Place `generate_changelog.py` (and optionally `changelog.sh` or `SKILL.md`) into your repository root or `.claude/skills/generate-changelog/`.

2. **Run the script**:
   ```bash
   python generate_changelog.py
   # or bash changelog.sh
   ```

3. **Commit your changelog**:
   ```bash
   git add CHANGELOG.md && git commit -m "docs: update changelog"
   ```

## 🏷️ Commit Classification

| Commit Prefix | CHANGELOG Section |
| :--- | :--- |
| `feat:` / `feat(scope):` / `add:` | **Added** |
| `fix:` / `fix(scope):` / `resolve:` | **Fixed** |
| `refactor:` / `chore:` / `style:` / `perf:` | **Changed** |
| `remove:` / `revert:` / `deprecate:` | **Removed** |

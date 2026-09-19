# 📝 Generate Changelog Skill & CLI

Automatically generates a structured `CHANGELOG.md` conforming to [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Conventional Commits](https://www.conventionalcommits.org/) from git history.

## 🚀 3-Step Quickstart

### Step 1: Install / Place the Skill
Copy `skills/generate-changelog/SKILL.md` into your project's `.claude/skills/` directory (or use directly in this repository).

### Step 2: Generate Changelog
Run either command from your project root:
```bash
# Option A: In Claude Code
/generate-changelog

# Option B: Terminal (Bash or Python)
bash changelog.sh
# or:
python scripts/generate_changelog.py
```

### Step 3: Review Output
Inspect your newly generated or prepended `CHANGELOG.md`.

---

## ⚙️ Features
- **Smart Categorization**: Sorts commits into `Added`, `Fixed`, `Changed`, `Removed`, and `Deprecated`.
- **Tag-Aware**: Automatically diffs commits from the latest git tag (`vX.Y.Z`) up to `HEAD`.
- **History-Preserving**: Neatly prepends new release sections without overwriting historical changelog entries.
- **Cross-Platform**: Works on Linux, macOS, and Windows.

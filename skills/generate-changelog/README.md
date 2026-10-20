# 📜 Structured Git Changelog Generator

Automatically generate a clean, categorized `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) from your git history. Supports Conventional Commits and standard semantic commit messages.

## 🚀 Quick Setup (3 Steps)

### Step 1: Download or copy script
Copy `generate_changelog.py` (or `changelog.sh`) into your repository root or scripts directory.

### Step 2: Run the generator
```bash
python3 generate_changelog.py
```
*(or `./changelog.sh`)*

### Step 3: (Optional) Specify version tag
```bash
python3 generate_changelog.py --version v1.2.0 --since v1.1.0
```

---

## 💡 Claude Code & Antigravity Agent Skill
If using Claude Code or Antigravity, place `SKILL.md` in your `.gemini/skills/generate-changelog/` or `.claude/skills/` directory to enable the `/generate-changelog` slash command.

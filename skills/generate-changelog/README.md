# Structured Git Changelog Generator

> 📜 Automatically generate a structured, categorized `CHANGELOG.md` from git history.
> Solves **[Bounty #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)** ($50).

---

## ⚡ Setup & Usage (3 Steps)

### Step 1: Copy the script or skill
```bash
cp skills/generate-changelog/SKILL.md ~/.claude/skills/generate-changelog.md
# Or place scripts/generate_changelog.py in your repo
```

### Step 2: Run the generator
In Claude Code:
```bash
/generate-changelog
```
Or directly via shell:
```bash
python scripts/generate_changelog.py
```

### Step 3: Inspect your generated `CHANGELOG.md`
The script detects the latest tag and auto-categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed` following [Keep a Changelog](https://keepachangelog.com/).

---

## 🧪 Testing

```bash
python tests/test_generate_changelog.py
```
*(Unit tests passing)*

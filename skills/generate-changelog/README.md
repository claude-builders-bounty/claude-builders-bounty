# Git Changelog Generator Skill

A lightweight, automated `CHANGELOG.md` generator from git history for Claude Code & bash environments.

## Features
- ✅ Zero external dependencies (pure bash + standard git)
- ✅ Auto-detects git tags or parses full history
- ✅ Categorizes into `Added`, `Fixed`, `Changed`, `Removed`
- ✅ Idempotent: prepends new release sections without overwriting past history

---

## Setup & Usage in 3 Steps

### 1. Install / Place in your project
Copy `changelog.sh` into your project root or scripts directory:
```bash
chmod +x changelog.sh
```

### 2. Generate Changelog
Run the script directly:
```bash
bash changelog.sh
```
*(Optionally specify an output file: `bash changelog.sh CUSTOM_CHANGELOG.md`)*

### 3. (Optional) Use as Claude Code Skill
Place `SKILL.md` in your project's `.agents/skills/generate-changelog/` or Claude Code skills directory. Trigger anytime by typing:
```text
/generate-changelog
```

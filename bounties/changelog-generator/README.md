# 📋 CHANGELOG Generator

Auto-generate a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

### 1️⃣ Add to project
Copy both files to your repo root:
```
changelog.sh     — standalone bash script
SKILL.md         — (optional) Claude Code skill
```

### 2️⃣ Run it
```bash
bash changelog.sh
```

Or inside Claude Code:
```
/generate-changelog
```

### 3️⃣ Customize (optional)
```bash
# From a specific tag
bash changelog.sh --since v1.0.0

# From a different repo
bash changelog.sh --repo /path/to/project
```

## Output

Generates `CHANGELOG.md` with commits auto-categorized into:
🚀 Added · 🔧 Fixed · 🔄 Changed · 🗑️ Removed · 📝 Documentation · 🧪 Testing · 📦 Other

## Sample

```markdown
# Changelog since v2.0.0

## [2026-05-07]

### 🚀 Added
- Add new dashboard widget (a1b2c3d)

### 🔧 Fixed
- Fix crash on empty state (e4f5g6h)
```

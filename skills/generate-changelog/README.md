# Generate Changelog Skill & Script

> Automatically generate and update a structured `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com) conventions from your git history.

---

## ⚡ Setup (3 Steps or Fewer)

### Step 1: Install Script or Skill
Copy the skill into your Claude Code skills directory or copy the script into your project:

```bash
# As a Claude Code skill:
cp -r skills/generate-changelog ~/.claude/skills/

# Or as a standalone project script:
cp scripts/changelog.sh ./changelog.sh && chmod +x ./changelog.sh
```

### Step 2: Run the Generator
Invoke via Claude Code command or directly in your terminal:

```bash
# Via bash script:
bash scripts/changelog.sh

# Or via cross-platform python:
python3 scripts/generate_changelog.py
```

### Step 3: Review `CHANGELOG.md`
Your `CHANGELOG.md` is automatically created or prepended with categorized entries (`Added`, `Fixed`, `Changed`, `Removed`) referencing commit hashes and authors.

---

## 🧪 Real-World Sample Output

See [`samples/CHANGELOG.sample.md`](../../samples/CHANGELOG.sample.md) for an output generated from actual repository commits.

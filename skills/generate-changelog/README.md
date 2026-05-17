# Changelog Generator — Claude Code Skill (Bounty #1)

> **$50 Bounty** — Automatically generate structured `CHANGELOG.md` from git history.

---

## What This Does

Running `/generate-changelog` (or `python generate_changelog.py`) will:

1. Find the latest git tag (or initial commit if no tags)
2. Fetch all commits since that tag
3. Auto-categorize into **Added / Fixed / Changed / Removed**
4. Prepend a new section to `CHANGELOG.md`

---

## Setup Instructions (3 Steps)

### Step 1: Copy Files to Your Project
```bash
# Copy these files into your project root
cp generate_changelog.py /your/project/
cp SKILL.md /your/project/.Claude/skills/generate-changelog/
```

### Step 2: Run It
```bash
# Option A: Claude Code command
/generate-changelog

# Option B: Direct Python
python generate_changelog.py
```

### Step 3: Commit the Result
```bash
git add CHANGELOG.md
git commit -m "chore: update CHANGELOG"
```

---

## Sample Output

After running on `claude-builders-bounty/claude-builders-bounty`:

```markdown
## [0.2.0] - 2026-05-17

### Added
- Bounty #5 n8n workflow (abc1234)
- Add CLAUDE.md template (def5678)

### Fixed
- Fix hook regex edge case (ghi9012)

### Changed
- Refactor PR review agent (jkl3456)
```

---

## Files

| File | Description |
|------|-------------|
| `generate_changelog.py` | Main Python script |
| `SKILL.md` | Claude Code skill definition |
| `CHANGELOG.md` | Sample output (this file) |

---

## Customization

- **Repo URL:** Edit the GitHub commit link format in `generate_changelog.py` (line ~90)
- **Versioning:** Auto-increments patch (e.g., `0.1.0` → `0.1.1`)
- **Categories:** Modify `categorize_commit()` to add custom rules

---

**Created for:** [claude-builders-bounty/claude-builders-bounty #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)  
**Bounty Amount:** $50  
**Status:** ✅ Ready for review

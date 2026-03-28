# Generate Changelog Skill

**Bounty:** claude-builders-bounty #1 | **Reward:** $50

## What This Is

A bash script + Claude Code SKILL.md that generates a structured `CHANGELOG.md` from git history, auto-categorising commits into Added / Fixed / Changed / Removed.

## 3-Step Setup

```bash
# 1. Copy the script
cp scripts/changelog/generate-changelog.sh /your/project/

# 2. Make it executable
chmod +x /your/project/generate-changelog.sh

# 3. Run (optionally pass a git tag)
cd /your/project
bash generate-changelog.sh        # from last tag
bash generate-changelog.sh v1.0.0 # from specific tag
```

## Files

| File | Description |
|------|-------------|
| `generate-changelog.sh` | Main script (bash, zero dependencies) |
| `SKILL.md` | Claude Code skill for `/generate-changelog` command |
| `SAMPLE_CHANGELOG.md` | Example output |

## Features

- ✅ Zero dependencies (pure bash + git + standard Unix tools)
- ✅ Conventional commit parsing (`feat:`, `fix:`, `chore:`, etc.)
- ✅ Falls back to heuristic categorization for non-conventional commits
- ✅ Tag-aware (uses last git tag by default)
- ✅ Markdown table format with commit hash + description
- ✅ Preserves existing CHANGELOG.md history
- ✅ Works on any git repository

## Test Evidence

See `SAMPLE_CHANGELOG.md` for generated output from a sample repository.

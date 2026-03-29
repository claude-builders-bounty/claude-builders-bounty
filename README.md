# SKILL: Generate a Structured CHANGELOG from Git History

Create a `SKILL.md` and `changelog.sh` that automatically generates a `CHANGELOG.md` from a project's git history.

## Files

- `SKILL.md` — Claude Code skill documentation
- `changelog.sh` — Bash script implementation

## Setup (3 Steps)

**Step 1 — Install**
```bash
# Copy changelog.sh to your project
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/skill/changelog-generator/changelog.sh -o changelog.sh
chmod +x changelog.sh
```

**Step 2 — Run**
```bash
# Generate changelog from last git tag
./changelog.sh

# Or from a specific tag
./changelog.sh --since-tag v1.0.0

# Output to custom file
./changelog.sh --output HISTORY.md
```

**Step 3 — Commit & Done**
```bash
git add CHANGELOG.md
git commit -m "docs: update changelog"
```

## Features

- Auto-categorizes commits: Added / Fixed / Changed / Removed / Security
- Uses conventional commit prefixes (feat:, fix:, refactor:, etc.)
- Falls back to content analysis for non-prefixed commits
- Outputs Keep a Changelog 1.0.0 compatible format
- Works with any git tag or from beginning of history

## Sample Output

See [`SAMPLE_CHANGELOG.md`](./SAMPLE_CHANGELOG.md) for an example output.

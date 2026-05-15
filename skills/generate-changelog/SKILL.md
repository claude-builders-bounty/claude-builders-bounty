---
name: generate-changelog
description: Generate a categorized CHANGELOG.md from git commits since the latest tag.
---

# Generate Changelog

Use this skill when the user asks to generate, refresh, or update a changelog for a git repository.

## Steps

1. Check the repository state:

```bash
git status --short
git tag --sort=-creatordate | head -5
```

2. Run the generator from the repository root:

```bash
python3 scripts/generate_changelog.py
```

3. Review the generated changelog:

```bash
git diff -- CHANGELOG.md
```

4. If the user only wants a preview, run:

```bash
python3 scripts/generate_changelog.py --dry-run
```

## Behavior

The script:
- Uses the latest git tag as the starting point.
- Falls back to all commits when no tag exists.
- Categorizes commits into Added, Fixed, Changed, and Removed.
- Writes a dated release block to CHANGELOG.md.
- Preserves existing changelog content below the new block.

## Options

```bash
python3 scripts/generate_changelog.py --from v1.2.3
python3 scripts/generate_changelog.py --output docs/CHANGELOG.md
python3 scripts/generate_changelog.py --dry-run
```

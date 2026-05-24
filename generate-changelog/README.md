# generate-changelog

Generate a structured `CHANGELOG.md` from git history. Auto-categorizes commits by type into Added / Fixed / Changed / Removed sections.

## Setup (3 steps)

1. **Copy** `generate-changelog/` into your project
2. **Run**: `python generate-changelog/changelog.py`
3. **Commit**: the generated `CHANGELOG.md`

## Options

```bash
python changelog.py --tag v1.0.0     # Start from a specific tag
python changelog.py --repo ../other  # Run on another repo
```

## Requirements

Python 3.6+ and git. Cross-platform (Windows, Mac, Linux).

## Claude Code Integration

Copy it as a skill:

```bash
cp -r generate-changelog ~/.claude/skills/
```

Then in Claude Code: `/generate-changelog`

## Output

Commits are categorized by conventional commit prefix:

| Prefix | Section |
|--------|---------|
| `feat:` `add:` `implement:` | **Added** |
| `fix:` `bugfix:` `hotfix:` | **Fixed** |
| `refactor:` `chore:` `update:` `bump:` | **Changed** |
| `remove:` `deprecate:` `delete:` | **Removed** |
| `docs:` `test:` `ci:` `style:` `perf:` | **Other** |

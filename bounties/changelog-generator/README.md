# Changelog Generator

Generate structured `CHANGELOG.md` from git history in 1 command.

## Quick Setup

```
1. Copy changelog.sh (or changelog.py) into your project
2. Run: bash changelog.sh
3. Commit the generated CHANGELOG.md
```

## Usage

```bash
# Bash version
bash changelog.sh

# Python version
python changelog.py

# Custom output path
python changelog.py docs/CHANGELOG.md

# Claude Code
/generate-changelog
```

## Output

Commits are auto-categorized based on conventional commit prefixes:

| Category | Keywords |
|----------|----------|
| Added | `feat:`, `add`, `feature`, `new` |
| Fixed | `fix:`, `bug`, `hotfix`, `patch` |
| Changed | Everything else (chore, refactor, docs, etc.) |
| Removed | `remove`, `delete`, `drop`, `deprecate` |

## Sample

Generated from [deep-research-agent](https://github.com/suoyinjv/deep-research-agent):

```markdown
# Changelog

## [0.1.0] - 2026-05-31

### Changed
- Cleanup (88e3ba0)
- Init (ad419a8)
```

## Requirements

- Git
- Bash 4.0+ **or** Python 3.6+

# generate-changelog

Automatically generate a structured `CHANGELOG.md` from your project's git history.

## Setup (3 steps)

1. **Copy** `scripts/generate_changelog.py` into your repo
2. **Run** `python3 scripts/generate_changelog.py`
3. **Done!** `CHANGELOG.md` is generated

## Requirements

- Python 3.6+
- Git

## What it does

- Detects the last git tag
- Fetches all commits since that tag
- Categorizes into: **Added**, **Fixed**, **Changed**, **Removed**
- Outputs a properly formatted `CHANGELOG.md` (Keep a Changelog spec)

## Categories

| Commit prefix | Category |
|--------------|----------|
| `feat:`, `add:` | Added |
| `fix:`, `bugfix:` | Fixed |
| `chore:`, `refactor:`, `change:` | Changed |
| `remove:`, `delete:` | Removed |

## Sample output

See [sample CHANGELOG.md](sample_changelog.md) for example output.

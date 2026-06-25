# CHANGELOG Generator Skill

Generates a structured CHANGELOG.md from a project's git history.

## Usage

```bash
python scripts/generate_changelog.py --repo . --output CHANGELOG.md
```

## How It Works

1. Finds the last git tag
2. Gets all commits since that tag
3. Categorizes commits: Added / Fixed / Changed / Removed
4. Outputs a properly formatted CHANGELOG.md

## Categories

- **Added**: feat, add, new, implement, create
- **Fixed**: fix, bugfix, patch, resolve, correct
- **Changed**: refactor, change, update, modify, improve, perf, style
- **Removed**: remove, delete, deprecate, drop

## Examples

```bash
# Generate changelog for current repo
python scripts/generate_changelog.py

# Generate for a specific repo
python scripts/generate_changelog.py --repo /path/to/repo

# Custom output file
python scripts/generate_changelog.py --output RELEASE_NOTES.md
```

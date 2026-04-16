# CHANGELOG Generator

Automatically generates a structured `CHANGELOG.md` from your project's git history using conventional commits.

## Usage

**One command:**
```
/generate-changelog
```

Or run directly:
```bash
bash changelog.sh
```

## What It Does

1. Finds commits since the last git tag (or all commits if no tags exist)
2. Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
3. Writes a properly formatted `CHANGELOG.md` with the current date
4. Preserves any existing CHANGELOG content below the new entry

## Categorization Rules

| Conventional Prefix | Section |
|---------------------|---------|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:`, `perf:`, `style:`, `build:`, `ci:`, `docs:`, `chore:` | Changed |
| `remove:`, `delete:`, `drop:`, `revert:` | Removed |
| Everything else | Changed |

## Options

```bash
bash changelog.sh --since v1.2.0    # Commits since a specific tag
bash changelog.sh --output CHANGES.md  # Write to a custom file
```

## Setup

Copy `changelog.sh` to your project root. No dependencies required — just bash and git.

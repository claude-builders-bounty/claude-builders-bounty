# Skill: Generate Changelog

Generate a structured `CHANGELOG.md` from a project's git history.

## Usage

```bash
# Generate changelog from last tag to HEAD
./generate-changelog.sh

# Generate from a specific tag
./generate-changelog.sh --from v1.0.0

# Generate for entire history
./generate-changelog.sh --all

# Custom output file
./generate-changelog.sh -o docs/CHANGES.md
```

## How it works

1. Determines the commit range (last tag → HEAD by default)
2. Parses each commit message using conventional commit format
3. Falls back to keyword matching for non-conventional commits
4. Categorizes into: Added / Fixed / Changed / Removed
5. Outputs a properly formatted `CHANGELOG.md`

## Conventional Commit Support

Recognizes: `feat:`, `fix:`, `refactor:`, `remove:`, `revert:`, `docs:`, `chore:`, `test:`, `perf:`, `build:`, `ci:`, `style:`

With scopes: `feat(auth): add login`, `fix(api): handle null response`

## Keyword Fallback

For commits without conventional prefixes:
- `add`, `added`, `new`, `create`, `implement` → Added
- `fix`, `fixed`, `bugfix`, `patch`, `hotfix` → Fixed
- `remove`, `removed`, `delete`, `drop` → Removed
- `refactor`, `change`, `update`, `modify`, `rename` → Changed

## Requirements

- `git` (any recent version)
- `python3` (3.6+)
- Run from within a git repository

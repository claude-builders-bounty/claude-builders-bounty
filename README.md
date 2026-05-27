# Generate Changelog from Git History

A Python CLI tool that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Setup (3 steps)

1. **Ensure Python 3.7+ and git are installed**
   ```bash
   python --version && git --version
   ```

2. **Run the script inside any git repo**
   ```bash
   python generate_changelog.py
   ```

3. **Done!** `CHANGELOG.md` is created/updated in your project root.

## Usage

```bash
# All commits (auto-prepends to existing CHANGELOG.md)
python generate_changelog.py

# Commits since a specific tag
python generate_changelog.py --since-tag v1.0

# Custom version label and output file
python generate_changelog.py --version v2.0 --output RELEASE_NOTES.md

# Preview without writing
python generate_changelog.py --dry-run
```

## How It Categorizes Commits

| Category | Keywords / Conventional Prefix |
|----------|-------------------------------|
| Added | add, new, create, feat, implement, support |
| Fixed | fix, bug, patch, hotfix, resolve |
| Changed | update, change, modify, refactor, improve |
| Removed | remove, delete, deprecate, drop |
| Docs | doc, readme, comment, changelog |
| Test | test, spec, ci, coverage |

Supports [Conventional Commits](https://www.conventionalcommits.org/) format — `feat:`, `fix:`, etc.

## Features

- **Zero dependencies** — pure Python stdlib
- **Robust parsing** — uses git's `%x1f`/`%x1e` separators (not fragile string delimiters)
- **Auto repo URL** — derives commit links from `git remote` (SSH and HTTPS)
- **Full SHA links** — commit URLs use full SHA for reliability
- **Line ending tolerant** — handles both `\n` and `\r\n`
- **Prepend mode** — new entries go above existing ones

## Sample Output

```markdown
# Changelog

## v3.2

### Added
- Add GitHub Actions badges — [abc1234](link) (Author, 2025-01-15)
- Create FUNDING.yml — [def5678](link) (Author, 2025-01-14)

### Fixed
- Fix CSV export encoding — [ghi9012](link) (Author, 2025-01-13)
```

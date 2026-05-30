# Generate Structured CHANGELOG from Git History

A Python script that automatically generates a structured `CHANGELOG.md` from a project's git history. Categorizes commits using [Conventional Commits](https://www.conventionalcommits.org/) format.

## Setup (3 steps)

1. **Copy the script** to your project:
   ```bash
   cp changelog/generate_changelog.py /path/to/your/project/
   ```

2. **Run the script** from your project root:
   ```bash
   python generate_changelog.py
   ```

3. **Done!** Your `CHANGELOG.md` is generated. Commit it.

## Usage

```bash
# Basic: generates CHANGELOG.md from last tag to HEAD
python generate_changelog.py

# Specify repository path
python generate_changelog.py --repo /path/to/repo

# Specify version label
python generate_changelog.py --version 2.0.0

# Start from a specific tag/branch
python generate_changelog.py --since v1.0.0

# Preview without writing
python generate_changelog.py --dry-run

# JSON output for tooling
python generate_changelog.py --json

# Custom output file
python generate_changelog.py --output RELEASES.md
```

## How It Works

1. Finds the most recent git tag (or uses `--since` if provided)
2. Fetches all commits between that tag and HEAD
3. Parses each commit message for conventional commit prefixes
4. Categorizes into: **Added**, **Fixed**, **Changed**, **Removed**, **Security**
5. Outputs formatted markdown to `CHANGELOG.md`

## Commit Convention Mapping

| Prefix | Category |
|--------|----------|
| `feat`, `feature` | Added |
| `fix`, `bugfix`, `hotfix` | Fixed |
| `refactor`, `chore`, `perf`, `docs`, `style`, `ci`, `build` | Changed |
| `remove`, `revert`, `delete`, `deprecate` | Removed |
| `security` | Security |

Non-conventional commits are categorized by keyword detection, defaulting to "Changed".

## Testing

```bash
cd changelog
python -m pytest test_generate_changelog.py -v
```

## Sample Output

```markdown
# Changelog

## Changes since v0.1.0 (2026-05-30)

**5 commits** categorized below.

### Added
- add user model ([`abc1234`](...))
- **api**: add pagination support ([`def5678`](...))

### Fixed
- resolve null pointer in auth ([`ghi9012`](...))

### Changed
- clean up service layer ([`jkl3456`](...))

### Removed
- delete legacy migration script ([`mno7890`](...))
```

## License

MIT

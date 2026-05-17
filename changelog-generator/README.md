# Changelog Generator

Automatically generate a structured `CHANGELOG.md` from your project's git history.

Commits are auto-categorized into **Added / Fixed / Changed / Removed** based on conventional commit prefixes and common keywords.

## Setup (3 steps)

### 1. Download

```bash
# Clone or just download changelog.sh
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog-generator/changelog.sh
```

### 2. Make it executable

```bash
chmod +x changelog.sh
```

### 3. Run it

```bash
# Generate changelog for the current repo (auto-detects last tag)
bash changelog.sh

# Or point it at any repo
bash changelog.sh /path/to/your/repo

# Custom options
bash changelog.sh . --tag v2.0.0 --output MY_CHANGELOG.md
```

That's it! A `CHANGELOG.md` will be created in the target directory.

## How It Works

1. Finds the last git tag in your repository
2. Collects all commits since that tag
3. Categorizes each commit by analyzing the message prefix:
   - **Added**: `feat`, `add`, `new`, `create`, `implement`, `introduce`, `support`
   - **Fixed**: `fix`, `bug`, `patch`, `resolve`, `hotfix`, `repair`, `correct`
   - **Changed**: `update`, `refactor`, `improve`, `rename`, `move`, `migrate`, `bump`, `upgrade`, `replace`, `modify`
   - **Removed**: `remove`, `delete`, `drop`, `deprecate`, `strip`, `eliminate`
   - **Other**: anything that doesn't match the above patterns
4. Strips conventional commit prefixes (e.g., `feat(scope):` → clean entry)
5. Outputs a properly formatted `CHANGELOG.md` with comparison links

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--tag TAG` | Generate changelog since this tag | Last git tag |
| `--output FILE` | Output filename | `CHANGELOG.md` |
| (positional) | Path to git repo | `.` (current dir) |

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.1.0] - 2025-05-17

### Added

- user authentication module
- dashboard widgets

### Fixed

- resolve login timeout issue
- correct timezone offset in scheduler

### Changed

- simplify database connection pool
- upgrade dependencies to latest versions

### Removed

- delete deprecated API endpoints
- mark legacy sync method as deprecated

### Other

- update CI configuration

[v1.1.0]: https://github.com/user/repo/compare/v1.0.0...v1.1.0
```

## Requirements

- Bash 4.0+
- Git

## License

MIT

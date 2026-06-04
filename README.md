# CHANGELOG Generator

Auto-generate structured `CHANGELOG.md` from your git history.

## Setup

1. **Clone or copy** `changelog.sh` to your project root
2. **Make it executable:** `chmod +x changelog.sh`
3. **Run it:** `./changelog.sh`

## How It Works

- Fetches commits since the last git tag
- Auto-categorizes based on conventional commit prefixes:
  - **Added** — `feat`, `add`, `new`, `introduce`, `implement`
  - **Fixed** — `fix`, `bugfix`, `hotfix`, `resolve`, `patch`
  - **Changed** — `update`, `change`, `modify`, `refactor`, `improve`
  - **Removed** — `remove`, `delete`, `drop`, `deprecate`
- Outputs a properly formatted `CHANGELOG.md`

## Example Output

\`\`\`markdown
# Changelog

## [Unreleased]

### Added
- feat: add user authentication
- implement infinite sequence iterator

### Fixed
- fix: resolve memory leak in cache

### Changed
- refactor: simplify route handlers
\`\`\`

## Requirements

- Git repository with commit history
- Bash (Linux/macOS/WSL)

## License

MIT

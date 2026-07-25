# generate-changelog — Claude Code Skill

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from git history.

## Usage

```
/generate-changelog
```

Or directly:

```bash
bash changelog.sh
```

## Features

- Fetches commits since the **last git tag**
- Auto-categorizes commits into: `Added`, `Fixed`, `Changed`, `Removed`
- Outputs a properly formatted `CHANGELOG.md`
- Follows [Conventional Commits](https://www.conventionalcommits.org/) parsing

## Setup (3 steps)

1. Copy `changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run: `./changelog.sh`

## Sample Output

```markdown
# Changelog

## [1.2.0] — 2026-06-23

### Added
- Add user authentication endpoint
- Add session management with refresh tokens

### Fixed
- Fix circular reference in Note model
- Fix memory leak in WebSocket handler

### Changed
- Upgrade to Next.js 15
- Refactor database connection pooling

### Removed
- Remove deprecated payment API
- Remove legacy admin panel
```

## Requirements

- Git 2.0+
- Bash 3.0+
- `jq` (optional, for JSON output)

## How It Works

1. Reads git tags sorted by version
2. Finds the latest tag (`v1.2.0` or `1.2.0`)
3. Collects all commits since that tag
4. Parses commit messages by conventional commit type:
   - `feat` → Added
   - `fix` → Fixed
   - `refactor`, `perf`, `build`, `docs`, `style`, `test`, `chore` → Changed
   - `remove`, `delete`, `deprecate` → Removed
5. Generates markdown with version header and categorized list
6. Writes to `CHANGELOG.md` (or stdout with `--stdout`)

## License

MIT

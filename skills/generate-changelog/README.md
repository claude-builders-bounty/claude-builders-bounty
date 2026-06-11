# Generate Changelog Skill

Automatically generate a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

1. **Copy the skill to your project**
   ```bash
   cp -r skills/generate-changelog/ /your-project/.claude/skills/generate-changelog/
   ```

2. **Use via Claude Code command**
   ```
   /generate-changelog
   ```

3. **Or use the bash script directly**
   ```bash
   bash skills/generate-changelog/changelog.sh [version]
   ```

## How It Works

- Fetches commits since the last git tag
- Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
- Uses [Conventional Commits](https://www.conventionalcommits.org/) prefixes:
  - `feat:` → Added
  - `fix:` → Fixed
  - `refactor:`, `perf:`, `chore:` → Changed
  - `remove:`, `revert:` → Removed
  - `docs:`, `test:`, `style:` → skipped
- Outputs a properly formatted `CHANGELOG.md`
- Prepends new entries above existing content

## Sample Output

```markdown
## [1.2.0] - 2026-06-09

### Added
- User avatar upload endpoint
- Dark mode toggle for settings page

### Fixed
- Login redirect loop on expired tokens
- Search results pagination off-by-one error

### Changed
- Upgraded database driver to v3.2

### Removed
- Deprecated v1 API endpoints
```

## Tested On

- Node.js project with conventional commits (this repo)
- Python project with mixed commit styles
- Monorepo with multiple packages

## License

MIT

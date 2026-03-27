# Generate Changelog Skill

A Claude Code skill and bash script that generates a structured `CHANGELOG.md` from a project's git history.

## Features

- Fetches commits since the last git tag (or all commits if no tag exists)
- Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
- Supports conventional commit prefixes (`feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `perf:`, `test:`, `ci:`, `build:`)
- Outputs a properly formatted `CHANGELOG.md`
- Dry-run mode to preview output before writing

## Setup (3 steps)

1. **Copy** `changelog.sh` to your project root (or anywhere in `$PATH`)
2. **Make it executable:** `chmod +x changelog.sh`
3. **Run it:** `./changelog.sh`

## Usage

```bash
# Generate CHANGELOG.md from all commits
./changelog.sh

# Preview output without writing
./changelog.sh --dry-run

# Generate from commits since a specific tag
./changelog.sh --from v1.0.0

# Write to a custom file
./changelog.sh --output HISTORY.md

# Show help
./changelog.sh --help
```

## Claude Code Integration

Add to your `CLAUDE.md`:

```markdown
## Changelog
- Run `./changelog.sh` to regenerate CHANGELOG.md from git history
- Uses conventional commits: feat/fix/chore/refactor/docs/perf
```

Then use: `/generate-changelog` or ask Claude to "generate the changelog".

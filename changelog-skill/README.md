# Changelog Generator

Generate structured `CHANGELOG.md` from git history with automatic categorization.

## Quick Start (3 steps)

1. **Copy** `changelog.sh` to your project root
2. **Make executable**: `chmod +x changelog.sh`
3. **Run**: `./changelog.sh`

That's it! Check your new `CHANGELOG.md`.

## Features

- ✅ Auto-categorizes commits: **Added** / **Fixed** / **Changed** / **Removed**
- ✅ Detects breaking changes
- ✅ Parses conventional commits (`feat:`, `fix:`, `refactor:`, etc.)
- ✅ Extracts PR numbers from `(#NNN)` patterns
- ✅ Works with or without git tags
- ✅ Zero dependencies (just bash + git)

## Usage

### Basic

```bash
./changelog.sh
```

Generates `CHANGELOG.md` in the current directory.

### Custom output file

```bash
./changelog.sh HISTORY.md
```

### In Claude Code

The accompanying `SKILL.md` enables `/generate-changelog` command in Claude Code.

## How It Works

1. Finds the last git tag (or uses all commits if no tags)
2. Reads commits in conventional commit format
3. Categorizes each commit by type:
   - `feat:` → **Added**
   - `fix:` → **Fixed**
   - `refactor:` / `perf:` → **Changed**
   - `docs:` / `chore:` / `build:` / `ci:` → **Changed**
   - `revert:` → **Removed**
   - `!` suffix or `BREAKING CHANGE:` → **⚠️ Breaking Changes**
4. Generates formatted Markdown

## Conventional Commits

This tool works best with [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(auth): add OAuth2 login flow
fix(api): handle null response from server (#123)
refactor(db): optimize query performance
feat!: change API response format
```

Non-conventional commits are categorized as **Changed**.

## Example Output

See [SAMPLE_CHANGELOG.md](./SAMPLE_CHANGELOG.md) for a real example.

## Requirements

- Git
- Bash 4.0+
- No external tools

## License

MIT

# generate-changelog

A zero-dependency CHANGELOG.md generator from git history.

## Setup (3 steps)

### 1. Copy the script

```bash
curl -sL -o changelog.sh https://raw.githubusercontent.com/your-repo/main/changelog.sh
chmod +x changelog.sh
```

### 2. Run it

```bash
./changelog.sh
```

This generates `CHANGELOG.md` in the current directory.

### 3. (Optional) Add to Claude Code

Add this alias to your `CLAUDE.md`:

```markdown
/generate-changelog = bash changelog.sh
```

Now Claude can run it via `/generate-changelog`.

## Features

- ✅ Zero dependencies (pure bash + git)
- ✅ Conventional commits support (feat:, fix:, refactor:, etc.)
- ✅ Auto-categorizes: Added / Fixed / Changed / Removed
- ✅ Keep a Changelog format
- ✅ Tag-aware (uses last tag as version)

## CLI Flags

| Flag | Description |
|------|-------------|
| `--stdout` | Output to stdout instead of file |
| `--since=<tag>` | Generate from specific tag |

## Example Output

```markdown
# Changelog

## [Unreleased] - 2026-06-18

### Added

- feat: add OAuth2 support (af2860c)
- feat: add rate limiter (122ac4c)

### Fixed

- fix: resolve memory leak in worker (1a2b3c4)
```

## License

MIT

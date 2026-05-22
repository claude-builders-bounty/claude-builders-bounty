# Changelog Generator

Auto-generates a structured `CHANGELOG.md` from git history using conventional commit prefixes.

## Setup

1. **Copy the skill** — Place `SKILL.md` into your `~/.claude/skills/` directory (create it if needed).
2. **Make the script executable** — Run `chmod +x generate-changelog.sh` in this directory.
3. **Use it** — In Claude Code, type `/generate-changelog`. Or run `./generate-changelog.sh` directly.

## How It Works

The tool reads commits since the last git tag and categorizes them by prefix:

| Prefix | Category |
|---|---|
| `feat:` `feature:` `add:` | **Added** |
| `fix:` `bugfix:` `patch:` | **Fixed** |
| `refactor:` `change:` `update:` `improve:` | **Changed** |
| `remove:` `delete:` `drop:` | **Removed** |
| `docs:` `test:` `ci:` `chore:` or no prefix | **Other** |

Scoped commits like `feat(auth): add login` render as: **auth**: add login.

## Options

```bash
# Generate with "Unreleased" header (default)
./generate-changelog.sh

# Generate with a specific version
./generate-changelog.sh v1.2.0
```

## Requirements

- Git
- Bash
- No external dependencies

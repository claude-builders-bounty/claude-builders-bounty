# Changelog Generator

A Claude Code skill that generates a structured CHANGELOG.md from git history.

## Setup (3 steps)

1. Copy the `skills/changelog-generator/` folder into your project
2. Make the script executable: `chmod +x skills/changelog-generator/changelog.sh`
3. Run it: `./skills/changelog-generator/changelog.sh`

## What it does

- Fetches commits since the last git tag (or all commits if no tags)
- Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
- Outputs a properly formatted CHANGELOG.md

## CLI Options

```bash
./skills/changelog-generator/changelog.sh --from v1.0.0 --to HEAD --output CHANGES.md --repo /path/to/repo
```

Or via environment variables:

```bash
CHANGELOG_FROM=v1.0.0 CHANGELOG_OUTPUT=CHANGES.md ./skills/changelog-generator/changelog.sh
```

## Commit Conventions

| Prefix | Section |
|--------|---------|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:`, `perf:`, `style:` | Changed |
| `remove:`, `delete:` | Removed |

Commits without a recognized prefix go to "Changed".

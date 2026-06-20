# Changelog Generator Skill

This skill generates a structured CHANGELOG.md from a project's git history.

## Usage

When asked to generate a changelog, run the `changelog.sh` script in the project root:

```bash
./skills/changelog-generator/changelog.sh
```

Or invoke via the `/generate-changelog` command if configured as a Claude Code slash command.

## How it works

1. Finds the latest git tag (or uses `--from` commit SHA if no tags exist)
2. Collects all commits since that reference
3. Parses commit messages using conventional commit patterns (`feat:`, `fix:`, `chore:`, etc.)
4. Categorizes into: Added, Fixed, Changed, Removed
5. Outputs a properly formatted CHANGELOG.md

## Configuration

The script accepts these optional environment variables:

- `CHANGELOG_FROM` — commit SHA or tag to start from (default: latest tag)
- `CHANGELOG_TO` — commit SHA or tag to end at (default: HEAD)
- `CHANGELOG_OUTPUT` — output file path (default: CHANGELOG.md)
- `CHANGELOG_REPO` — path to git repo (default: current directory)

## Example

```bash
CHANGELOG_FROM=v1.0.0 CHANGELOG_OUTPUT=CHANGES.md ./skills/changelog-generator/changelog.sh
```

## Commit Message Conventions

The parser recognizes these prefixes:

| Prefix | Section |
|--------|---------|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:`, `perf:`, `style:` | Changed |
| `remove:`, `delete:` | Removed |
| `docs:`, `test:`, `chore:`, `ci:` | (excluded by default) |

Commits without a recognized prefix are placed in the "Changed" section.

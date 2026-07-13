# Skill: Generate CHANGELOG

**Trigger:** `/generate-changelog`

**Description:** Parse conventional commits from git history and generate a structured CHANGELOG.md grouped by version tags or date ranges.

## Usage

```
/generate-changelog [--from <tag>] [--to <tag>] [--output <file>] [--group-by <type|scope>]
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--from <tag>` | first tag | Start tag (inclusive) |
| `--to <tag>` | HEAD | End tag (inclusive) |
| `--output <file>` | CHANGELOG.md | Output file path |
| `--group-by <type|scope>` | type | Group commits by type or scope |

## Supported Conventional Commit Types

| Type | Emoji | Section |
|------|-------|---------|
| `feat` | ✨ | Features |
| `fix` | 🐛 | Bug Fixes |
| `docs` | 📝 | Documentation |
| `chore` | 🧹 | Chores |
| `refactor` | ♻️ | Refactors |
| `test` | 🧪 | Tests |
| `perf` | ⚡ | Performance |
| `style` | 🎨 | Style |

## Implementation

1. Run `generate-changelog.sh` from the repository root with the provided options
2. Parse the output and write it to the specified output file (default: CHANGELOG.md)
3. If the file already exists, prepend new entries above the existing content

## Examples

```
/generate-changelog
/generate-changelog --from v1.0.0 --to v2.0.0
/generate-changelog --output docs/CHANGELOG.md --group-by scope
/generate-changelog --from v1.0.0
```

# Generate CHANGELOG Skill

Generate a structured `CHANGELOG.md` from a project's git history, auto-categorized by change type.

## Trigger

Say `/generate-changelog` or ask:
- "generate a changelog from git history"
- "create a CHANGELOG from commits since the last tag"

## What it does

1. Fetches commits since the last git tag (or from a specified tag with `--from`)
2. Parses conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.) and keyword matches
3. Categorizes into: Added, Fixed, Changed, Removed, Other
4. Generates a clean `CHANGELOG.md`

## Usage

The skill runs `python3 changelog.py` behind the scenes.

| Option | Description |
|--------|-------------|
| (no args) | Generate from last tag |
| `--from v1.0` | Generate from a specific tag |
| `--all` | Include all commits (no tag filter) |
| `--output FILE.md` | Custom output path |
| `--stdout` | Print to stdout only |

### Examples

```
/generate-changelog                          # Since last tag
/generate-changelog --from v1.0.0            # From specific tag
/generate-changelog --all                    # Full history
/generate-changelog --output docs/CHANGELOG.md
```

## Requirements

- Python 3.9+
- Git initialized in the project directory

## Setup

1. Place this directory in your project or `.claude/skills/`
2. The skill is ready to use — no additional install needed

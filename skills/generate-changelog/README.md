# Generate Changelog Skill

This skill creates a structured `CHANGELOG.md` from commits since the last git tag, grouped into `Added`, `Fixed`, `Changed`, and `Removed`.

## Setup

1. Copy this folder into a project or run it directly from this repository.
2. Run `python skills/generate-changelog/changelog.py --repo /path/to/repo`.
3. Review the generated `CHANGELOG.md` before committing it.

## Usage

```bash
python skills/generate-changelog/changelog.py --repo . --output CHANGELOG.md
```

Use `--since v1.2.0` to generate from a specific tag or revision instead of auto-detecting the latest tag.

## Output Rules

- Conventional commit prefixes are honored when present.
- Fixes and regressions go under `Fixed`.
- New capabilities go under `Added`.
- Removals, deletions, drops, and deprecations go under `Removed`.
- Everything else is grouped under `Changed`.

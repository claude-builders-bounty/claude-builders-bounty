# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup

1. Copy this folder into a git repository.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md`.

## Options

```bash
bash changelog.sh --since v1.2.0 --output CHANGELOG.md
```

## Output Sections

- `Added`
- `Fixed`
- `Changed`
- `Removed`

The generator understands Conventional Commit prefixes and falls back to keyword matching for plain commit subjects.

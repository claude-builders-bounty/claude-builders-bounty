# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup

1. Copy `changelog.sh`, `scripts/generate_changelog.py`, and `skills/generate-changelog/SKILL.md` into your repository.
2. Run `bash changelog.sh` from the repository root.
3. Review and commit the generated `CHANGELOG.md`.

## Usage

Preview without writing:

```bash
bash changelog.sh --stdout
```

Write `CHANGELOG.md`:

```bash
bash changelog.sh
```

Use a specific revision or tag instead of the latest tag:

```bash
bash changelog.sh --since v1.2.0
```

The generator writes four sections: `Added`, `Fixed`, `Changed`, and `Removed`.

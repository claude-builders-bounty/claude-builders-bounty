# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from commits since the last git tag.

## Setup in 3 Steps

1. Copy this repository's `changelog.sh` and `skills/generate-changelog` folder into your project.
2. Run `bash changelog.sh` from the project root.
3. Review the generated `CHANGELOG.md` before release.

## Options

```bash
bash changelog.sh --from-ref v1.0.0 --to-ref HEAD
bash changelog.sh --output docs/CHANGELOG.md
bash changelog.sh --stdout
```

The script categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.

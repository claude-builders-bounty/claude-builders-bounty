# Generate Changelog Skill

This Claude Code skill creates a Markdown changelog from git commits since the latest tag.

```bash
./skills/generate-changelog/changelog.sh [output-file] [version]
```

By default, it writes `CHANGELOG.md` with the version heading `Unreleased`. The Python generator can also be run directly:

```bash
python3 skills/generate-changelog/generate_changelog.py CHANGELOG.md v1.0.0
```

Commit subjects are grouped into `Added`, `Fixed`, `Changed`, and `Removed`. Conventional commit prefixes drive the category, while uncategorized commits fall back to `Changed`.

See [examples/sample-output.md](examples/sample-output.md) for the output format.

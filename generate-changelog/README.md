# Generate Changelog Skill

Creates a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup / usage

```bash
chmod +x generate-changelog/changelog.sh
./generate-changelog/changelog.sh
```

Optional output path:

```bash
./generate-changelog/changelog.sh docs/CHANGELOG.md
```

The script categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed` using common commit prefixes and keywords. If the repo has no tags, it uses the full git history.

---
name: generate-changelog
description: Generate a structured CHANGELOG.md from the current Git repository history. Use when the user asks for /generate-changelog, changelog generation, release notes from commits, or categorized changes since the last git tag.
---

# Generate Changelog

Use `scripts/changelog.sh` to create a `CHANGELOG.md` from Git history.

## Workflow

1. Run from the repository that needs a changelog:

   ```bash
   bash path/to/skills/generate-changelog/scripts/changelog.sh
   ```

2. By default, the script uses commits after the latest reachable git tag and writes `CHANGELOG.md`.

3. Review the generated file for project-specific wording before final delivery.

## Options

```bash
bash scripts/changelog.sh --output CHANGELOG.md
bash scripts/changelog.sh --from v1.2.3 --to HEAD
bash scripts/changelog.sh --repo /path/to/repo --output /tmp/CHANGELOG.md
```

## Categories

The script groups commits into `Added`, `Fixed`, `Changed`, and `Removed` using common Conventional Commit prefixes and plain-English verbs. Breaking changes are called out separately when the subject contains `!` after the type or mentions `BREAKING CHANGE`.

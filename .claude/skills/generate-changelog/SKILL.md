---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag.
---

# Generate Changelog

Use this skill when a repository needs a release-ready `CHANGELOG.md` generated from git history.

## Workflow

Run the project script from the repository root:

```bash
bash changelog.sh
```

The script detects the latest git tag, gathers commits after that tag, categorizes them into `Added`, `Fixed`, `Changed`, and `Removed`, and writes `CHANGELOG.md`.

If there are no tags, it uses the full repository history and states that in the output.

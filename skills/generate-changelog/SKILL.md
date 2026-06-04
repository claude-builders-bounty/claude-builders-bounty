---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a git repository's commit history, grouped into Added, Fixed, Changed, and Removed sections.
---

# Generate Changelog

Use this skill when a user asks to create or refresh a `CHANGELOG.md` from git history.

## Workflow

1. Confirm the target directory is a git repository.
2. Run the bundled generator from the repository root:

```bash
bash changelog.sh
```

3. Review `CHANGELOG.md` and adjust the version heading if the user supplied a release version:

```bash
bash changelog.sh --version v1.2.3
```

## Options

- `--since <ref>`: use a specific tag, branch, or commit instead of the latest tag.
- `--output <path>`: write to a different changelog path.
- `--stdout`: print the generated changelog without writing a file.
- `--skip-empty-sections`: omit categories with no commits.

The generator categorizes conventional commits and common English commit verbs into `Added`, `Fixed`, `Changed`, and `Removed`.

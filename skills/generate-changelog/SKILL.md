---
name: generate-changelog
description: Generate a structured CHANGELOG.md from local git history since the latest tag.
---

# Generate Changelog

Use this skill when the user asks for `/generate-changelog` or wants a `CHANGELOG.md` generated from git history.

## Workflow

1. Confirm the current directory is the target git repository.
2. Run `bash changelog.sh` from this skill directory, or copy `changelog.sh` into the target repo and run it there.
3. Review the generated `CHANGELOG.md` and adjust wording only when commit subjects are unclear.

## Behavior

- Detects the latest reachable git tag with `git describe --tags --abbrev=0`.
- Uses commits in `latest-tag..HEAD`, or full history when no tag exists.
- Categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a markdown changelog with commit short hashes and commit dates.

## Command

```bash
bash changelog.sh
```

Optional output path:

```bash
bash changelog.sh --output docs/CHANGELOG.md
```

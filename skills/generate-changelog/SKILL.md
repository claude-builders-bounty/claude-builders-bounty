# Generate Changelog

Use this skill when a project needs a structured `CHANGELOG.md` generated from git history.

## Command

Run:

```bash
bash scripts/changelog.sh
```

This writes `CHANGELOG.md` in the current repository. To write somewhere else:

```bash
bash scripts/changelog.sh /tmp/CHANGELOG.md
```

## Behavior

- Reads commits since the latest git tag.
- Falls back to the full repository history when no tag exists.
- Skips merge commits.
- Groups entries into `Added`, `Fixed`, `Changed`, and `Removed`.
- Includes short commit hashes beside each entry.

## Review Checklist

1. Run the script from the repository root.
2. Inspect the generated sections for sensible grouping.
3. Commit the generated `CHANGELOG.md` only if it matches the release scope.

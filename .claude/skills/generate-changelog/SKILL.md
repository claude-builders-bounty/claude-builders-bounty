---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when a repository needs a structured changelog generated from Git commit history.

## Steps

1. Run the checked-in generator from the repository root:

   ```bash
   bash changelog.sh
   ```

2. Inspect `CHANGELOG.md` and confirm it includes these sections:

   - `Added`
   - `Fixed`
   - `Changed`
   - `Removed`

3. If you need a different output path, pass it as the first argument:

   ```bash
   bash changelog.sh docs/CHANGELOG.md
   ```

## Validation

For a deterministic smoke test, run:

```bash
bash generate-changelog/test-changelog.sh ./changelog.sh
```

The smoke test creates a temporary tagged repository and verifies that only commits since the latest tag are included.

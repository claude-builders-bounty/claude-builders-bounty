---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the last tag.
---

# Generate Changelog

Use this skill when the user asks for `/generate-changelog`, "generate a changelog", or "write CHANGELOG.md from git history".

## Workflow

1. Run the bundled script from the repository root:

   ```bash
   bash skills/generate-changelog/changelog.sh
   ```

2. Review the generated `CHANGELOG.md` sections:

   - `Added`
   - `Fixed`
   - `Changed`
   - `Removed`

3. If the repository has no git tags, the script uses all commits reachable from `HEAD`. If a tag exists, it uses commits since the latest tag.

The bash script delegates to `changelog.py`, so the same implementation can also
be run directly with `python3 skills/generate-changelog/changelog.py`.

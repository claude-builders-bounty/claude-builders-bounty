# Generate Changelog

`changelog.sh` creates a structured `CHANGELOG.md` from git history.

## Setup

1. Copy `changelog.sh` and `skills/generate-changelog/SKILL.md` into the target
   repository.
2. Run `bash changelog.sh` from the repository root.
3. Review `CHANGELOG.md` before release and adjust ambiguous entries if needed.

## Behavior

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Uses commits since that tag, or all reachable commits when no tag exists.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes `CHANGELOG.md` by default, or a custom path when passed as the first
  argument.

Example:

```bash
bash changelog.sh docs/sample-CHANGELOG.md
```

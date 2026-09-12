# generate-changelog

A Claude Code skill (and standalone bash script) that generates a structured `CHANGELOG.md` from your git history.

## Setup

1. **Copy this folder** into your project's `.claude/skills/` directory (or load it via `claude` and referencing `SKILL.md` directly).
2. **Make the script executable** (one-time):
   ```bash
   chmod +x skills/generate-changelog/scripts/changelog.sh
   ```
3. **Run it** from your repo root — either ask Claude Code to `/generate-changelog`, or run the script directly:
   ```bash
   bash skills/generate-changelog/scripts/changelog.sh
   ```

## What it does

- Fetches commits since your last git tag (or a range you specify)
- Categorizes each commit into `Added`, `Fixed`, `Changed`, or `Removed` — using Conventional Commit prefixes where present, and keyword matching as a fallback
- Writes (or prepends to) `CHANGELOG.md`

## Example

```bash
bash skills/generate-changelog/scripts/changelog.sh v1.2.0
```

See `sample-output/CHANGELOG.md` in this PR for a real example generated from a test repo with mixed commit styles.

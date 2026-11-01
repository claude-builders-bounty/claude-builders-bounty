---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, categorized into Added/Fixed/Changed/Removed.
---

# Generate Changelog Skill

## Command
`/generate-changelog` or `bash changelog.sh [output_file] [since_ref]`

## What it does
1. Finds the last git tag (or first commit if none).
2. Collects all commits since that ref.
3. Categorizes each by conventional-commit prefix:
   - `feat:` / `add:` → **Added**
   - `fix:` / `bugfix:` → **Fixed**
   - `remove:` / `deprecate:` → **Removed**
   - `chore:` / `refactor:` / `perf:` / `docs:` / `style:` / `test:` / `ci:` / `build:` → **Changed**
   - anything else → **Other**
4. Writes a Keep-a-Changelog style `CHANGELOG.md`.

## Usage
```bash
bash changelog.sh                # writes CHANGELOG.md, since last tag
bash changelog.sh OUT.md v1.2.0  # custom output and starting ref
```

## Installation (3 steps)
1. Copy `changelog.sh` to your project root.
2. `chmod +x changelog.sh`
3. Run `bash changelog.sh`.

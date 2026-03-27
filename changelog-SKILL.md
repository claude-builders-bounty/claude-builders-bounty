# SKILL.md — Generate Changelog from Git History

## When to use

Trigger when the user says:
- "generate changelog"
- "create a changelog"
- "what changed since last release"
- "summarize git history"

## How it works

Run `bash /path/to/changelog.sh [output_file]` to generate a structured `CHANGELOG.md`.

The script:
1. Finds the last git tag (or uses all commits if none exist)
2. Reads every commit message since that tag
3. Categorizes by conventional-commit prefix:
   - `feat:` → **Added**
   - `fix:` → **Fixed**
   - `chore:`, `refactor:`, `docs:`, `perf:`, `style:`, `ci:`, `build:` → **Changed**
   - `remove:`, `delete:`, `deprecate:` → **Removed**
4. Writes `CHANGELOG.md` with proper Markdown headings

## Usage

```bash
# Generate CHANGELOG.md in current repo
bash changelog.sh

# Custom output path
bash changelog.sh docs/CHANGELOG.md
```

## Options

- Output file: defaults to `CHANGELOG.md`
- Supports conventional commits (`feat:`, `fix:`, etc.)
- Falls back gracefully when no tags exist

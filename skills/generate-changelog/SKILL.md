# generate-changelog

Generate a structured `CHANGELOG.md` from this project's git history.

## Trigger

Use `/generate-changelog` in Claude Code, or run directly:

```bash
bash generate-changelog.sh [output-file]
```

## What it does

1. Finds the most recent git tag (falls back to full history if no tags exist)
2. Reads every commit since that tag
3. Auto-categorises each commit using conventional-commit prefixes:
   - **✨ Added** — `feat:`, `add:`, `new:`
   - **🐛 Fixed** — `fix:`, `bug:`, `patch:`, `hotfix:`
   - **🔧 Changed** — `refactor:`, `chore:`, `perf:`, `docs:`, `style:`, etc.
   - **🗑️ Removed** — `remove:`, `delete:`, `drop:`, `deprecate:`
   - **📝 Other** — anything that doesn't match a prefix
4. Writes a properly formatted `CHANGELOG.md` (Keep a Changelog spec)

## Usage in Claude Code

When the user says `/generate-changelog`, run:

```bash
bash "$(dirname "$0")/generate-changelog.sh"
```

Then show the user the path to the generated file and a summary of how many commits were categorised in each section.

## Arguments

| Argument | Default | Description |
|---|---|---|
| `output-file` | `CHANGELOG.md` | Path to write the changelog |

## Requirements

- git ≥ 2.x
- bash ≥ 3.2 (macOS compatible)
- No external dependencies

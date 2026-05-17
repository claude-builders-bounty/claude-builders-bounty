# changelog.sh — Structured CHANGELOG Generator

Generate a structured `CHANGELOG.md` from any project's git history.

## Setup (2 commands)

```bash
chmod +x changelog.sh
# Done — no dependencies beyond git
```

## Usage

```bash
# From project root
bash changelog.sh

# Or specify path and output
bash changelog.sh /path/to/repo docs/CHANGELOG.md
```

## Features

- **Fetches commits since last git tag** (falls back to first commit if no tags)
- **Auto-categorizes** into: Added, Fixed, Changed, Removed
- **Conventional Commits aware** — `feat:`/`add:` → Added, `fix:` → Fixed, `remove:` → Removed
- **Skips merge commits** automatically
- **Zero dependencies** — just `bash` and `git`

## Sample Output

See `test-output.md` for a real example generated from a large production repo (574 lines).

## How it works

1. Finds the most recent git tag
2. Collects all non-merge commits since that tag
3. Classifies each commit message by prefix or content
4. Writes structured markdown to `CHANGELOG.md`

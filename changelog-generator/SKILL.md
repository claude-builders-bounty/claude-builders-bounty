# /generate-changelog — Structured CHANGELOG.md from git history

Fetches commits since the last git tag and auto-categorizes them into:
Added, Fixed, Changed, Removed.

## Usage

In Claude Code, just say: "generate a changelog" or "/generate-changelog"

Or run directly:
```bash
bash generate-changelog.sh
bash generate-changelog.sh --tag v1.0.0
bash generate-changelog.sh --output docs/CHANGELOG.md
```

## How It Works

1. Finds the most recent git tag (or uses `--tag` override)
2. Collects all non-merge commits since that tag
3. Categorizes commits:
   - **Added** — `feat:`, `add:`, `create:`, `implement:`, or keywords like "new", "feature"
   - **Fixed** — `fix:`, `bug:`, `patch:`, or keywords like "crash", "error", "broken"
   - **Changed** — `refactor:`, `update:`, `chore:`, `docs:`, `style:`, `perf:`, etc.
   - **Removed** — `remove:`, `drop:`, `delete:`, `deprecate:`
4. Writes structured `CHANGELOG.md` with version, date, and categorized entries

## Rules

- Always use this script — never manually construct a changelog entry
- Run after tagging a release: `bash generate-changelog.sh --tag v1.2.3`
- The script handles empty ranges gracefully (no commits = no output)
- Categorization uses conventional commit prefixes first, falls back to keyword heuristics
- Output is always `CHANGELOG.md` unless `--output` is specified

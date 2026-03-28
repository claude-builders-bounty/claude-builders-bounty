# Generate CHANGELOG from git history

Automatically generate a structured `CHANGELOG.md` from this project's git history, categorized into Added / Fixed / Changed / Removed sections.

## Usage

```
/generate-changelog
/generate-changelog --since v1.2.3
/generate-changelog --dry-run
/generate-changelog --output HISTORY.md
```

## Steps

1. Check that we are inside a git repository (run `git rev-parse --is-inside-work-tree`).
2. Find the last git tag with `git describe --tags --abbrev=0 HEAD`.
3. Run `bash ~/.claude/commands/generate-changelog/changelog.sh` with any flags the user specified.
4. If `--dry-run` was requested, print the output to the user directly.
5. Otherwise, confirm that `CHANGELOG.md` was written and show the first 30 lines.
6. Ask the user if they want to commit the changelog: `git add CHANGELOG.md && git commit -m "docs: update CHANGELOG for VERSION"`.

## Flags

| Flag | Description |
|------|-------------|
| `--since TAG` | Start from a specific tag instead of the last one |
| `--output FILE` | Write to a different file (default: `CHANGELOG.md`) |
| `--dry-run` | Print to stdout, do not write a file |

## Notes

- Commits are auto-categorized by conventional commit prefix: `feat` → Added, `fix` → Fixed, `remove/delete` → Removed, everything else → Changed
- Commit SHAs are linked to GitHub if a remote URL is detected
- Merge commits are excluded automatically
- If no tags exist, all commits are included with an `[Unreleased]` header

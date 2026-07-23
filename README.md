# Changelog Generator — Claude Code Bounty ($50)

Generate a structured `CHANGELOG.md` from any git repository's history.

## Usage (3 steps)

1. **Download** `changelog.py`
2. **Run** in your repo: `python changelog.py`
3. **Done** — `CHANGELOG.md` appears

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--repo <path>` | `.` | Target git repository |
| `--output <file>` | `CHANGELOG.md` | Output path |

## Example

```bash
python changelog.py --repo ../my-project --output CHANGELOG.md
```

### Sample output

```markdown
# Changelog

## [v14.2.6] - 2026-03-03

### Changed
- chore: add changeset (#854)
- Switch package manager to pnpm 10 (#853)

### Fixed
- replace clipboardy with tinyclip (#848)
```

## Requirements

- Python 3.8+
- `git` on PATH

## Implementation

`changelog.py` runs `git describe --tags` to find the last release, then categorizes commits by their first word (`add/feat` → Added, `fix/bug` → Fixed, `remove/delete` → Removed, everything else → Changed).

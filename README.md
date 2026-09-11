# Git Changelog Generator

Generate a structured `CHANGELOG.md` from Git history.

## Setup

1. Download `changelog.sh`.
2. Make it executable: `chmod +x changelog.sh`.
3. Run `./changelog.sh`.

The script uses the latest Git tag as the starting point. If no tag exists, it processes the repository's complete history.

Commit prefixes are categorized as:

- `feat:` / `add:` → Added
- `fix:` / `bug:` → Fixed
- `remove:` / `delete:` / `revert:` → Removed
- other commits → Changed

## Tests

Run:

```bash
./tests/test_changelog.sh
```

The tests use temporary Git repositories and do not require network access.

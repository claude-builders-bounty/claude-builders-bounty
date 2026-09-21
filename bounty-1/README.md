# Structured changelog generator

Three-step setup:

1. Copy `changelog.sh` to the root of any Git repository.
2. Run `chmod +x changelog.sh`.
3. Run `bash changelog.sh` (or `bash changelog.sh path/to/CHANGELOG.md`).

The script finds the most recent reachable Git tag, reads non-merge commits after that tag, maps them to **Added / Fixed / Changed / Removed**, and writes a deterministic Markdown changelog. If the repository has no tag, it uses all reachable commits.

## Categorization

- `feat`, `add`, `create`, `introduce`, `new` → Added
- `fix`, `bugfix`, `repair` → Fixed
- `remove`, `delete`, `drop` → Removed
- everything else → Changed

See `sample-output.md` for an example and `test_changelog.py` for the regression test.

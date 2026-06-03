# Generate Changelog

Creates a structured `CHANGELOG.md` from git history and groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.

## Setup

1. Copy `changelog.sh` into a git repository.
2. Run `bash changelog.sh` or use `/generate-changelog` in Claude Code.
3. Review and commit the generated `CHANGELOG.md`.

## Usage

```bash
bash changelog.sh
```

Write to a custom path:

```bash
bash changelog.sh docs/CHANGELOG.md
```

## Behavior

- Uses commits since the latest git tag.
- Falls back to all reachable history when the repository has no tags.
- Keeps all four sections in the output, using `_No entries._` for empty sections.
- Strips common conventional commit prefixes from displayed subjects while keeping short SHAs and dates.

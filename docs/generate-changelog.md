# Generate Changelog

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Run `./changelog.sh --stdout` to preview.
2. Run `./changelog.sh` to write `CHANGELOG.md`.
3. Commit the generated changelog after review.

## Options

```bash
./changelog.sh --since v1.2.0 --to HEAD --output CHANGELOG.md
```

The generator groups non-merge commits into:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

Conventional commits such as `feat:`, `fix:`, `docs:`, and `refactor:` are recognized. Keyword-based fallback classification is used for ordinary commit subjects.

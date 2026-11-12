# changelog.sh

Generate a structured `CHANGELOG.md` from git history, categorized by
conventional-commit prefix into **Added / Fixed / Changed / Removed**.

## Setup (3 steps)

1. Copy `changelog.sh` into your repo root (it needs `git` + bash).
2. Run `bash changelog.sh` — commits since the last tag land in `CHANGELOG.md`.
3. Commit the generated file.

## Options

- `--output FILE` — write somewhere other than `CHANGELOG.md`
- `--from REF` — use an explicit range start instead of last tag

## Sample output

See `sample_CHANGELOG.md` — generated on a real repository with
`bash changelog.sh --from HEAD~15`.

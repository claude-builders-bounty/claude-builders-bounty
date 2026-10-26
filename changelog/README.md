# changelog.sh — structured CHANGELOG from git history

A zero-dependency bash skill that generates a Conventional-Commits-style structured CHANGELOG from any git repository.

## What it does
- Reads git history (from the last tag by default, or `--since`/`--until`)
- Groups commits into **Added / Changed / Fixed / Removed / Docs / Refactor / Chore** using conventional commit prefixes (`feat:`, `fix:`, `perf:`, `refactor:`, `docs:`, `chore:`, `revert:`) plus keyword heuristics
- Emits a clean Markdown CHANGELOG with per-commit hashes, authors, and dates
- `--full` includes all commits (no tag boundary)

## Usage
```bash
bash changelog.sh                 # from the last tag in the current repo
bash changelog.sh --full          # entire history
bash changelog.sh --since 2026-01-01
bash changelog.sh > CHANGELOG.md
```

## Requirements
- bash 4+, git
- no other dependencies

## Tested on
- synthetic repo (13 commits, mixed prefixes) — correct grouping, tag boundary respected
- psf/black (50 commits, real history) — sample output in `sample-output.md`

# generate-changelog

Zero-dependency changelog generator: a structured `CHANGELOG.md` from
git history, in the categories **Added / Fixed / Changed / Removed**.

Single engine, pure Python stdlib — no third-party packages, no bash
classification logic to drift out of sync. `changelog.sh` is a thin
wrapper around it, so both entry points the bounty asks for work:
`/generate-changelog` (via `SKILL.md`) and `bash changelog.sh`.

## Quick start (3 steps)

1. Copy `skills/generate-changelog/` into your project (or run it in place).
2. Run `bash changelog.sh` — or `python3 generate_changelog.py`.
3. Review the generated `CHANGELOG.md` and commit it.

## Usage

```bash
python3 generate_changelog.py                          # since last tag -> CHANGELOG.md
bash changelog.sh --dry-run                            # print to stdout, write nothing
python3 generate_changelog.py --since v1.0.0           # explicit starting ref
python3 generate_changelog.py --version 1.2.0 --output docs/CHANGELOG.md
python3 generate_changelog.py --show-hashes            # append short SHAs
python3 generate_changelog.py --include-merges         # merge commits are skipped by default
```

## How commits are classified

First match wins, in this order:

1. `BREAKING CHANGE` in the body, or `!` after the type (`feat!:`) →
   `Changed`, prefixed `⚠ BREAKING: `.
2. Conventional-Commit type: `feat` → Added; `fix` / `security` → Fixed;
   `remove` / `delete` / `drop` / `deprecate` → Removed; `refactor` /
   `perf` / `chore` / `build` / `ci` / `docs` / `style` / `test` /
   `revert` / `change` / `update` / `bump` / `deps` → Changed.
3. Free-text keywords, checked **Removed → Fixed → Added → Changed**,
   so "remove the fix" is not misfiled as a fix.
4. Anything else → Changed. Nothing is silently dropped.
5. `Merge ...` commits skipped by default; `Revert "..."` kept as
   `Revert: <original>` under Changed; exact duplicate subjects
   (case-insensitive) de-duplicated; `type(scope): description` renders
   as `Description (scope)`.

Output follows [Keep a Changelog](https://keepachangelog.com/), section
label `Unreleased` by default. See `SKILL.md` for the full spec.

## Files

| File | What it is |
|---|---|
| `generate_changelog.py` | The engine (stdlib only) |
| `changelog.sh` | Thin wrapper: `bash changelog.sh` |
| `SKILL.md` | Claude Code skill definition |
| `README.md` | This file |
| `tests/test_generate_changelog.py` | 40+ unit + integration tests |
| `SAMPLE_CHANGELOG.md` | Real output, pallets/markupsafe |

## Tests

```bash
python3 -m unittest discover -s tests -v
python3 -m pytest tests/ -q   # optional, if pytest is installed
```

## Requirements

`python3` (3.8+) and `git`. Nothing else.

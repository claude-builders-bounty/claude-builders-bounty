# generate-changelog

A zero-dependency Bash script (+ Claude Code skill) that generates a categorized
`CHANGELOG.md` from your git history — commits since the last tag, grouped into
**Added / Fixed / Changed / Removed** using conventional-commit prefixes.

## Setup (3 steps)

1. **Drop the files in your repo** — copy `changelog.sh` and `SKILL.md` into your project.
2. **Run it** — `bash changelog.sh` (or `/generate-changelog` in Claude Code).
3. **Commit the result** — a `CHANGELOG.md` is written to the repo root.

## Usage

```bash
bash changelog.sh                       # commits since last tag -> CHANGELOG.md
bash changelog.sh --since v1.2.0        # commits since a specific ref
bash changelog.sh --out docs/CHANGELOG.md
```

Works on any repo with git + bash. If no tags exist, it uses full history from
the root commit. See `SAMPLE-CHANGELOG.md` for real output from this repo's history.

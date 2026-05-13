# /generate-changelog

Generate a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

1. Copy this folder to your project at `.claude/skills/generate-changelog/`
2. Copy `changelog.sh` to your project root (next to `.git/`)
3. Run `/generate-changelog` in Claude Code (or run `bash changelog.sh`)

## Notes

- By default it uses commits since the last git tag. If your repo has no tags, it uses the full history.
- You can pass options like `--since v1.2.3` or `--output docs/CHANGELOG.md`.

## Sample output

See `examples/CHANGELOG.sample.md` (generated from `cli/cli`).

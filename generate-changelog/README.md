# Generate Changelog

Generate a structured `CHANGELOG.md` from git history.

## Setup in 3 steps

1. Copy `changelog.sh` and `scripts/generate_changelog.py` into the root of your git repository.
2. Run `bash changelog.sh` to generate `CHANGELOG.md` from commits since the latest tag.
3. Review the output with `git diff -- CHANGELOG.md`.

## Usage

```bash
bash changelog.sh
bash changelog.sh --from v1.0.0
bash changelog.sh --output docs/CHANGELOG.md
bash changelog.sh --dry-run
```

## Claude Code skill

Copy `skills/generate-changelog/SKILL.md` into your Claude Code skills directory, then run `/generate-changelog` in Claude Code.

## Output sections

Commits are auto-categorized into:

- Added
- Fixed
- Changed
- Removed

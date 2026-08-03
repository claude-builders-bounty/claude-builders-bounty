# generate-changelog

Generate a structured `CHANGELOG.md` from git history since the last tag.

## Setup (3 steps)

1. Copy `changelog.sh` into your project (or keep this folder as-is).
2. From a git repo, run: `bash changelog.sh`
3. Open the generated `CHANGELOG.md`

Optional Claude Code skill: copy `.claude/skills/generate-changelog/` into your project, then use `/generate-changelog`.

## What it does

- Reads commits since the latest git tag (or full history if none)
- Sorts them into **Added / Fixed / Changed / Removed**
- Writes a clean Markdown changelog

See `SAMPLE_CHANGELOG.md` for output tested on a real GitHub repo.

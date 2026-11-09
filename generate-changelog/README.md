# generate-changelog

Claude Code skill: structured `CHANGELOG.md` from git history —
`Added` / `Fixed` / `Changed` / `Removed`, Keep a Changelog style.

## Setup (3 steps)

1. Copy the `generate-changelog/` folder into your project (or `~/.claude/skills/`).
2. In Claude Code, run `/generate-changelog` — or from a terminal:
   ```bash
   bash generate-changelog/scripts/changelog.sh
   ```
3. Review `CHANGELOG.md` at the repo root. Done.

## Requirements

- git, bash. No other dependencies.

## Usage

```bash
bash scripts/changelog.sh            # since the latest tag, writes CHANGELOG.md
bash scripts/changelog.sh v1.2.0     # since a specific tag/branch/commit
bash scripts/changelog.sh | cat      # piped: prints to stdout, writes nothing
bash scripts/changelog.sh --stdout   # force stdout output
```

The script is deterministic: merge commits skipped, duplicates deduped,
existing `CHANGELOG.md` content preserved (new section prepended).
Works on bash 3.2+ (macOS default), Linux, Git Bash on Windows.

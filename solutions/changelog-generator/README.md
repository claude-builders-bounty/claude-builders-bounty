# CHANGELOG Generator

Automatically generate a structured `CHANGELOG.md` from your git history.

## Setup (3 steps)

1. Copy `changelog.sh` to your project root
2. Run `bash changelog.sh`
3. Review the generated `CHANGELOG.md`

## Features

- Auto-categorizes commits into Added / Fixed / Changed / Removed
- Follows [Keep a Changelog](https://keepachangelog.com) format
- Works with conventional commits and free-form messages
- Detects last tag automatically (or specify with `--since`)
- Includes commit hashes for traceability

## Claude Code Skill

Copy `SKILL.md` to your `.claude/skills/` directory to use via `/generate-changelog` command.

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--since TAG` | Generate since specific tag | Last tag |
| `--output FILE` | Output filename | CHANGELOG.md |

## Sample Output

See [sample-output.md](sample-output.md) for an example generated from a real repository.

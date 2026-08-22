# changelog.sh — structured CHANGELOG generator

Generates a `CHANGELOG.md` from git history, auto-categorized by Conventional Commits.

## Setup (3 steps)

1. Copy `changelog.sh` (and `SKILL.md` for Claude Code users) into your project root.
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `bash changelog.sh` — done, `CHANGELOG.md` appears.

## Usage

```bash
bash changelog.sh                 # write CHANGELOG.md
bash changelog.sh --stdout        # print to stdout
bash changelog.sh --since v1.2.3  # commits after a specific tag
```

In Claude Code, the skill is invoked with the `/generate-changelog` command (requires SKILL.md in `.claude/skills/generate-changelog/`).

## How it works

- Finds the last git tag (`git describe --tags --abbrev=0`); falls back to full history if no tags exist
- Collects commits in range `last_tag..HEAD`
- Categorizes by Conventional Commit type:

| Type | Section |
|---|---|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:` `chore:` `docs:` `test:` `perf:` `style:` `build:` `ci:` | Changed |
| `revert:` `remove:` `delete:` | Removed |
| `security:` | Security |
| `deprecate:` | Deprecated |
| no prefix | Changed |

- Merge commits are skipped
- Output follows the Keep a Changelog format with a compare link when a tag exists

## Requirements

- bash 4+ (for associative arrays)
- git

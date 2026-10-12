# generate-changelog

Claude Code skill + CLI that builds a Keep-a-Changelog `CHANGELOG.md` from git history since the last tag.

## Setup (3 steps)

1. Copy this folder to `~/.claude/skills/generate-changelog/` (personal) or `.claude/skills/generate-changelog/` (project).
2. `chmod +x changelog.sh scripts/generate.py`
3. In any git repo run: `bash ~/.claude/skills/generate-changelog/changelog.sh`

That's it — needs only `git` and `python3`.

## Usage

```bash
# default: since latest tag → CHANGELOG.md
bash changelog.sh

# specific range / title
bash changelog.sh --since v1.2.0 --title 1.3.0

# prepend into an existing changelog
bash changelog.sh --prepend

# dry-run
bash changelog.sh --dry-run
```

Invoke inside Claude Code as `/generate-changelog`.

## Acceptance mapping

| Criterion | How |
|-----------|-----|
| `/generate-changelog` or `bash changelog.sh` | Skill name + bash entrypoint |
| Commits since last tag | `git describe --tags --abbrev=0` then `tag..HEAD` |
| Added / Fixed / Changed / Removed | Conventional Commits + heuristics |
| Formatted `CHANGELOG.md` | Keep a Changelog sections |
| Real-repo sample | `examples/sample-CHANGELOG.md` (commander.js) |
| README ≤ 3 steps | This file |

## License

MIT — same as the bounty board repo.

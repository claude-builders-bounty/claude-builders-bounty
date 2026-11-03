# generate-changelog — Claude Code skill

Generates a structured `CHANGELOG.md` from git history: commits since the last
tag, auto-grouped into Breaking Changes / Added / Fixed / Changed / Removed.
The script is stdlib-only Python (Windows / Linux / macOS) and also works as a
plain CLI without Claude Code.

## Setup in 3 steps

1. Copy this folder to `.claude/skills/generate-changelog/` in your project
   (or `~/.claude/skills/generate-changelog/` to use it everywhere).
2. In Claude Code run `/generate-changelog`, or just ask
   "generate a changelog for this repo".
3. Without Claude Code: `python .claude/skills/generate-changelog/generate_changelog.py -o CHANGELOG.md`

## Verify it works

```bash
python test_generate_changelog.py   # or: pytest test_generate_changelog.py
```

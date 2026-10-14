# generate-changelog

Generates a structured `CHANGELOG.md` (Added / Fixed / Changed / Removed)
from git commits since the last tag. Pure bash + git, no dependencies.

## Setup (3 steps)
1. Copy `skills/generate-changelog/` into your repo (or `~/.claude/skills/`).
2. From the repo root run `bash skills/generate-changelog/changelog.sh`
   (options: `-v VERSION`, `-o FILE`, `-r REPO_DIR`).
3. Or in Claude Code type `/generate-changelog`.

Categorisation: `feat/add/new/implement` → Added; `fix/bug/resolve` → Fixed;
`remove/delete/drop/revert` → Removed; everything else → Changed.
Run `bash test.sh` for the self-test. See `examples/CHANGELOG.sample.md`
(generated from this very repo).

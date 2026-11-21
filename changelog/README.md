# changelog.sh

Generate a structured `CHANGELOG.md` from git history — commits since
the last tag bucketed into Added / Fixed / Changed / Removed.

## Setup (3 steps)

1. Save `changelog.sh` anywhere in your repo (or `PATH`).
2. `chmod +x changelog.sh`
3. Run `bash changelog.sh` — done, `CHANGELOG.md` is written.

## Usage

```bash
bash changelog.sh            # writes ./CHANGELOG.md
bash changelog.sh NOTES.md   # custom output path
```

Commits are collected from `git describe --tags --abbrev=0..HEAD`
(all commits when the repo has no tags, merges excluded) and sorted by
conventional-commit type or subject keywords:

- **Added** — `feat:`, add/implement/introduce/support
- **Fixed** — `fix:`, bugfix/hotfix/patch/resolve/correct
- **Changed** — `chore:`-style updates: update/upgrade/refactor/improve/optimize/migrate/rename
- **Removed** — remove/drop/delete/deprecate/revert
- **Other** — everything else, kept visible rather than dropped

`sample-output.md` shows real output from a tagged repo with 8 commits
covering every bucket.

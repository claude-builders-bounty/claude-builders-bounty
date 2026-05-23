# generate-changelog (bash)

Generate a structured `CHANGELOG.md` from git history, grouped into `Added`, `Fixed`, `Changed`, and `Removed`.

## Setup + Usage (3 steps)
1. Copy `changelog.sh` into your git repo and make it executable: `chmod +x changelog.sh`
2. Run: `./changelog.sh` (or `./changelog.sh path/to/CHANGELOG.md`)
3. Commit the generated `CHANGELOG.md`

## Notes
- If tags exist, it uses commits from `last_tag..HEAD`.
- If no tags exist, it uses all commits and labels section as `Initial Release`.
- Merge commits are excluded for cleaner entries.

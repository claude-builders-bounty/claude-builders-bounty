# Git changelog generator

`changelog.sh` creates a structured `CHANGELOG.md` from commits since the last
git tag. Conventional prefixes map to `Added`, `Fixed`, `Changed`, and
`Removed`; unrecognised commits go to `Changed`.

## Setup and use (3 steps)

1. Copy `changelog.sh` into a git repository and make it executable:
   `chmod +x changelog.sh`.
2. Run `./changelog.sh` (or pass an output path such as
   `./changelog.sh docs/CHANGELOG.md`).
3. Review the generated `Unreleased` section and commit the file.

The script uses the latest reachable tag as the start point. If no tag exists,
it uses the repository's root commit. Commit links use the configured `origin`
remote when available; the commit text remains useful when no remote exists.

## Categories

`feat`, `feature`, `add`, `new`, and `create` become **Added**; `fix`, `bug`,
`bugfix`, and `hotfix` become **Fixed**; `remove`, `delete`, and `drop` become
**Removed**. Other subjects become **Changed**.

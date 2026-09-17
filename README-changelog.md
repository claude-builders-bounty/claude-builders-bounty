# Git changelog generator

This standalone `changelog.sh` turns commits since the latest tag into a structured
`CHANGELOG.md`. It uses only Git and Bash.

## Use

1. Copy `changelog.sh` into a Git repository and make it executable.
2. Run `./changelog.sh CHANGELOG.md`.
3. Review the generated `CHANGELOG.md` and commit it.

Commit subjects are grouped by prefix: `feat:`/`add:` → Added, `fix:` → Fixed,
`remove:`/`breaking:` → Removed, and all other subjects → Changed. If no tag exists,
the complete history is used. Pass a repository path as the second argument when
running the script from elsewhere.

# Changelog Generator

A small, dependency-free Bash utility that turns commits since the latest Git tag into a structured `CHANGELOG.md`.

## Setup and use

1. Copy `changelog.sh` into your repository and make it executable: `chmod +x changelog.sh`.
2. Run `./changelog.sh` (or `./changelog.sh docs/CHANGELOG.md`).
3. Review the generated Markdown and commit it.

The script uses the latest reachable tag as the baseline. If no tag exists, it includes all commits on the current branch. Conventional prefixes are grouped as follows: `feat`/`add` → Added, `fix`/`bug` → Fixed, `remove`/`delete` → Removed, and everything else → Changed. Each entry includes the short commit hash.

## Example

From a repository tagged `v1.0.0`, run:

```bash
./changelog.sh
```

The output is written to `CHANGELOG.md` and contains Added, Fixed, Changed, and Removed sections only when commits exist in that category.

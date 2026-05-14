# Changelog generator

A small Bash utility that creates a structured `CHANGELOG.md` from git history since the latest tag.

## Setup and usage in 3 steps

1. Copy `changelog.sh` into any git repository and make it executable:
   ```bash
   chmod +x changelog.sh
   ```
2. Run it from the repository root:
   ```bash
   ./changelog.sh
   ```
3. Review and commit the generated `CHANGELOG.md`.

The script detects the latest git tag with `git describe --tags --abbrev=0`. If no tag exists, it uses the full repository history. Commits are grouped into `Added`, `Fixed`, `Changed`, and `Removed` using common Conventional Commit prefixes and fallback keyword matching.

# Generate a structured CHANGELOG

This repository-local tool creates a Keep-a-Changelog-style `CHANGELOG.md`
from git history using only Python 3 and git.

## Setup and use

1. Copy `changelog.py` and `changelog.sh` into your project.
2. Run `bash changelog.sh` (or `python3 changelog.py`).
3. Review `CHANGELOG.md` and commit it.

The default boundary is the newest git tag. When a repository has no tags, the
full history is used. Every output includes `Added`, `Fixed`, `Changed`, and
`Removed` sections, including an explicit empty marker when a category has no
matching commits. Use `--stdout` for a preview and `--from-tag TAG` to override
the boundary.

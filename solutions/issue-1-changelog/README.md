# Git Changelog Generator

Generate a structured `CHANGELOG.md` from Git commits since the most recent tag reachable from `HEAD`. The generator uses only Python's standard library and Git; it does not execute commit message contents.

## Setup and use

1. Copy `changelog.py` and `changelog.sh` into your Git repository.
2. Run `bash changelog.sh` from the repository root (or `python3 changelog.py`).
3. Review the generated `CHANGELOG.md` and edit it before release.

The generator falls back to all commits from the repository root when no reachable tag exists. Conventional `feat`, `fix`, `remove`, and `deprecate` commits map to **Added**, **Fixed**, and **Removed**; other types and untyped subjects map to **Changed**. `!` marks a breaking change.

By default, the command creates a new `CHANGELOG.md` and fails if that file already exists, preserving existing release history. Pass `--force` only when you intend to replace it, for example `bash changelog.sh --force`.

To select another repository or output path, use `python3 changelog.py --repo /path/to/repo --output /path/to/CHANGELOG.md`.

## Example

`examples/sample-output.md` includes a generated sample from a public GitHub repository, with the repository URL, exact HEAD, and reachable-tag status recorded for reproducibility.

## Tests

Run `python3 -m unittest -v`.

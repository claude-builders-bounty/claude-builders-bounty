# Generate Changelog

Use this skill when the user asks for `/generate-changelog`, a changelog, release notes, or a summary of git commits since the last tag.

## Workflow

1. Confirm the current working directory is a git repository.
2. Run `python changelog.py --dry-run` to preview the changelog, or `bash changelog.sh --dry-run` when Bash is available.
3. If the output looks correct, run `python changelog.py` or `bash changelog.sh` to write `CHANGELOG.md`.

## Behavior

- Finds the latest git tag with `git describe --tags --abbrev=0`.
- Uses all commits when the repository has no tags.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Keeps the output reviewable and deterministic.

## Options

- `--since <ref>`: choose the starting tag or commit.
- `--output <path>`: choose a different output file.
- `--dry-run`: print without writing.
- `--no-hashes`: omit short commit hashes.

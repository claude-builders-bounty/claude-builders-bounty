# Generate Changelog

Create a structured `CHANGELOG.md` from git commits in 3 steps:

1. Copy `changelog.py` and `changelog.sh` into the root of a git repository.
2. Run `python changelog.py` or `bash changelog.sh`.
3. Review the generated `CHANGELOG.md` before committing it.

Optional flags:

- `--since v1.2.0` starts from a specific tag or ref.
- `--output docs/CHANGELOG.md` writes to a custom path.
- `--dry-run` prints the changelog without writing a file.
- `--no-hashes` removes short commit hashes from the bullets.

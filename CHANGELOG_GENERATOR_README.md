# Changelog Generator

Use `changelog.sh` to create a structured `CHANGELOG.md` from git commits since
the latest tag. If the repository has no tags, it uses the full commit history.

1. Copy `changelog.sh` into any git repository.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md` before committing it.

The script categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`
using common commit prefixes such as `feat:`, `fix:`, `docs:`, and `remove:`.
See [examples/CHANGELOG.sample.md](examples/CHANGELOG.sample.md) for output
generated from this repository.

# Generate Changelog

Generate a structured `CHANGELOG.md` from git commits since the latest tag. The output uses the sections required by the bounty: `Added`, `Fixed`, `Changed`, and `Removed`.

## Setup

1. Copy `changelog.sh` and the `tools/generate-changelog/` directory into the root of a git repository.
2. Run `bash changelog.sh` to write `CHANGELOG.md`.
3. Review the generated file, then commit it with the release or maintenance PR.

## Usage

```bash
bash changelog.sh
```

Useful options:

- `--repo path/to/repo` inspects a different local git repository.
- `--output path/to/CHANGELOG.md` writes to a custom path.
- `--since-tag v1.2.3` overrides latest-tag detection.
- `--version 1.3.0` changes the heading from `Unreleased`.
- `--stdout` prints the changelog without writing a file.

## Categorization

The generator first checks Conventional Commit prefixes such as `feat:`, `fix:`, `docs:`, and `remove:`. If there is no prefix, it falls back to the first verb in the subject, such as `add`, `fix`, `update`, or `delete`. Subjects that do not match a specific rule go into `Changed` so every commit is represented.

If the repository has no tags, the generator uses the full repository history and says that clearly in the changelog.

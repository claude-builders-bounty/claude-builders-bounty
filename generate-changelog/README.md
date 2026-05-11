# Generate Changelog

Generate a structured `CHANGELOG.md` from git history using a dependency-free Bash script.

## Setup

1. Copy `changelog.sh` and the `generate-changelog` folder into any git repository.
2. Run `bash changelog.sh` from the repository root.
3. Review the generated `CHANGELOG.md` before committing it.

## Usage

```bash
bash changelog.sh
```

Useful options:

```bash
bash changelog.sh --dry-run
bash changelog.sh --output RELEASE_NOTES.md
bash changelog.sh --since v1.2.3
bash changelog.sh --version 1.3.0
```

The script finds commits since the latest git tag by default. If the repository has no tags, it uses the full commit history. Commits are grouped into `Added`, `Fixed`, `Changed`, and `Removed` sections using conventional commit types and common release-note keywords.

See `sample-output.md` for a real run against `octocat/Spoon-Knife`.

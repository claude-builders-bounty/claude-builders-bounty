# Generate Changelog

`changelog.sh` generates a structured `CHANGELOG.md` from the commits in the current git repository. It finds the latest reachable git tag, reads commits from that tag to `HEAD`, and groups commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.

## Setup

1. Copy `changelog.sh` and the `generate-changelog/` directory into any git repository.
2. Run `bash changelog.sh` from the repository root.
3. Review and commit the generated `CHANGELOG.md`.

## Usage

```bash
bash changelog.sh
```

Write to a custom file:

```bash
bash changelog.sh docs/CHANGELOG.md
```

Show help:

```bash
bash changelog.sh --help
```

## Categorization

- `Added`: commit subjects that look like features, additions, new support, creation, or implementation.
- `Fixed`: commit subjects that mention fixes, bugs, patches, repairs, or resolved issues.
- `Changed`: refactors, docs, chores, updates, improvements, and uncategorized commits.
- `Removed`: commit subjects that mention removals, deletions, drops, or deprecations.

The script strips common Conventional Commit prefixes such as `feat:`, `fix(scope):`, and `refactor!:` before writing the changelog entry.

## Sample Output

See `sample-output.md` for output generated against this GitHub repository.

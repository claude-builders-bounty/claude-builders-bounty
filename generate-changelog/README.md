# Generate Changelog

Small dependency-free changelog generator for Claude Code projects and regular Git repositories.

It reads the current repository history, finds commits since the latest Git tag, groups them into `Added`, `Fixed`, `Changed`, and `Removed`, then writes a formatted `CHANGELOG.md`.

## Setup

1. Copy the `generate-changelog` folder into your project.
2. Run `bash generate-changelog/changelog.sh` from the project root.
3. Review and commit the generated `CHANGELOG.md`.

## Usage

```bash
bash generate-changelog/changelog.sh
```

Optional flags:

```bash
python generate-changelog/generate_changelog.py --output CHANGELOG.md
python generate-changelog/generate_changelog.py --since v1.2.0 --version v1.3.0
python generate-changelog/generate_changelog.py --dry-run
```

## Categorization Rules

- `Added`: `feat`, `add`, `new`, `introduce`
- `Fixed`: `fix`, `bug`, `patch`, `repair`, `resolve`
- `Changed`: `change`, `refactor`, `docs`, `chore`, `perf`, `style`, `test`, `build`, `ci`
- `Removed`: `remove`, `delete`, `drop`, `deprecate`

The matcher prefers Conventional Commit prefixes, then falls back to practical keywords in the subject line.

## Git Range

- If the repository has tags, the script uses commits after the latest tag.
- If no tag exists, it uses all commits in the repository.
- Merge commits are skipped to keep the changelog focused on user-facing work.

## Sample Output

See [sample-output.md](sample-output.md) for a generated example.

## Testing

```bash
python -m unittest generate-changelog/test_generate_changelog.py
python -m py_compile generate-changelog/generate_changelog.py
```

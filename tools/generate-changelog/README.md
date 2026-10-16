# Git changelog generator

Generate a Markdown `CHANGELOG.md` from commit subjects after the nearest tag reachable from `HEAD`.
No GitHub tokens, APIs, additional Python packages, or paid services are used.

## Setup and run (3 steps)

1. Install [Git](https://git-scm.com/downloads) and Bash (Git for Windows includes Git Bash).
2. From any Git repository root, run `bash /path/to/changelog.sh` (or run `bash changelog.sh` while inside this tool's folder in the same repository).
3. Read the generated `CHANGELOG.md` at that repository's root.

To process another local Git repository without moving the script: `bash changelog.sh --repo /path/to/repo`.
The tool refuses to replace an existing `CHANGELOG.md` unless you explicitly pass `--force`.
Use `--output custom.md` to choose another file, e.g. for a non-destructive preview.

## Classification

| Section | Conventional-commit subjects | Other subjects |
|---|---|---|
| Added | `feat`, `feature`, `add` | begins `add`, `create`, `introduce` |
| Fixed | `fix`, `bugfix`, `hotfix` | contains `fix`, `fixed`, `bugfix`, `hotfix` as words |
| Changed | `docs`, `refactor`, `perf`, `test`, `chore`, `style`, `ci`, `build`, `change`, `update` | fallback |
| Removed | `remove`, `delete`, `drop` | begins `remove`, `delete`, `drop` |

Merge commits are excluded. If the repository has no reachable Git tag, all non-merge commits are used. A tagged HEAD yields empty sections rather than inventing changes. Only Git log subjects are read, not executed.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests use only temporary, locally created Git repositories. They check tag boundaries, classifications, merge handling, no-tag behavior, command-injection safety, no-overwrite, custom output, and error handling.

To test against an **actual public GitHub repository** and save a real sample for the PR, run:

```bash
bash tests/verify_public_repo.sh
```

That test requires internet access, clones an external public repository into a temporary directory, and writes the generated sample to `examples/CHANGELOG_FROM_PUBLIC_REPO.md`. It never pushes or edits the remote repository. It is not required for normal use.

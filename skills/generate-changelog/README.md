# Generate Changelog

Create a structured `CHANGELOG.md` from commits since the most recent git tag.

## Setup

1. Copy `changelog.sh` and `skills/generate-changelog/` into the repository you want to document.
2. Run `bash changelog.sh --output CHANGELOG.md`.
3. Review the categories, then commit the generated `CHANGELOG.md`.

## Usage

Local git repository:

```bash
bash changelog.sh --output CHANGELOG.md
```

Public GitHub repository, useful for testing or CI without a clone:

```bash
bash changelog.sh --repo owner/name --dry-run
```

Useful options:

- `--since-tag v1.2.3` uses a specific tag instead of auto-detecting the latest tag.
- `--max-commits 50` limits the number of commits included and must be at least 1.
- `--dry-run` prints the changelog instead of writing a file.
- `GITHUB_TOKEN` raises the GitHub API rate limit for `--repo` mode.

In GitHub API mode the generator resolves the repository's real default branch before comparing it with the latest tag, rather than assuming the branch is named `main` or that `HEAD` is a valid remote ref.

## Categorization

The generator maps commits into Keep a Changelog-style sections:

- `Added`: `feat:`, `feature:`, and add/create/introduce subjects.
- `Fixed`: `fix:`, `bugfix:`, `security:`, and repair/prevent/correct subjects.
- `Removed`: `remove:`, `delete:`, `drop:`, and deprecate subjects.
- `Changed`: refactors, chores, docs, tests, and anything that is not clearly one of the above.

## Verification

Run the regression suite:

```bash
cd skills/generate-changelog
python -m unittest -v test_changelog.py
```

The suite includes real temporary git repositories, not only mocked commit objects. It proves that the latest tag is detected, only post-tag commits are included, empty commit bodies remain parseable, all four required categories are produced, and `--dry-run` does not create `CHANGELOG.md`. It also verifies GitHub compare requests use the repository's explicit default branch.

The repository includes `.github/workflows/test-generate-changelog.yml`, which runs these tests, compiles the Python entrypoint, and smoke-tests the repo-root `changelog.sh` command on every push to the submission branch.

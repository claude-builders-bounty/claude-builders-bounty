# Generate a changelog

Requires Git, Bash, and Python 3.9 or later. No Python packages are needed.

## Setup and run

1. Clone this repository (or copy `changelog.sh` and `scripts/generate_changelog.py`, retaining that directory layout).
2. From your project's working tree, run `bash /path/to/changelog.sh`. Alternatively, run `bash changelog.sh --repo /path/to/project` from this repository.
3. Review the generated `CHANGELOG.md` in your project's root.

## Behavior

The generator reads local Git history from the nearest reachable tag to `HEAD`, excluding the tagged commit. It supports annotated and lightweight tags. With no reachable tag, it includes all commits. Merge commits are included, and each commit appears once. It does not change Git branches, tags, or commits.

If you need remote changes, fetch them before running the script. A shallow clone is rejected with the command needed to obtain complete history; CI checkouts should use `fetch-depth: 0`.

Conventional `feat`/`feature` commits and ordinary “Add”, “Introduce”, or “Implement” subjects become **Added**. `fix`/`bugfix`/`hotfix`/`patch` and “Fix”, “Resolve”, or “Repair” become **Fixed**. Explicit removals become **Removed**, including `feat!: remove ...`. Everything else becomes **Changed**, including refactors, dependency updates, deprecations that do not remove anything, and reverts. Subjects remain visible so the classification is easy to review.

Output contains all four sections, with `_No changes._` for empty categories. Commit subjects are escaped as Markdown text and carry a short commit ID. No commit message is executed.

Only the block between `<!-- git-changelog:begin -->` and `<!-- git-changelog:end -->` is refreshed. Existing released sections and handwritten notes remain outside that block. Rerunning with unchanged history produces identical content. Missing or duplicated markers and multiple Unreleased sections fail without replacing the file. The file is replaced atomically and existing permissions are retained.

## Options

```bash
# Preview without modifying any file:
bash changelog.sh --repo /path/to/project --stdout

# Use another filename, relative to the project's root:
bash changelog.sh --repo /path/to/project --output RELEASE_NOTES.md
```

## Validation

```bash
python3 -m unittest discover -s tests -v
bash -n changelog.sh
```

The tests create temporary real Git repositories and cover tag boundaries, unrelated tags, all four categories, empty/untagged histories, repeated runs, existing releases and manual notes, malformed input, output permissions, symlinks, shallow clones, and literal shell/Markdown characters.

The included [sample](../examples/requests.CHANGELOG.md) was generated from [psf/requests](https://github.com/psf/requests) at `611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60`, using the 29 commits after `v2.34.2`. [Source metadata](../examples/requests-source.json) records the exact tag commit and output checksum. To reproduce:

```bash
git clone https://github.com/psf/requests.git /tmp/requests-changelog-example
git -C /tmp/requests-changelog-example checkout 611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60
bash changelog.sh --repo /tmp/requests-changelog-example --stdout
```

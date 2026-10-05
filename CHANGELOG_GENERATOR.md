# Structured changelog generator

Python 3.9+ and Git are required. No Python packages, model API keys, or network requests are needed to generate a changelog.

## Setup and use (three steps)

1. Copy `changelog.py` and `changelog.sh` into your project (keep them together).
2. From that project run `bash changelog.sh`. On Windows without Bash, run `python changelog.py`.
3. Review the generated `CHANGELOG.md`. For later regeneration, use `bash changelog.sh --force`; this intentionally replaces the file, so preserve any hand-written release history separately.

To process another local repository: `bash changelog.sh --repo /path/to/repo --output CHANGELOG.md`. The output path is relative to that repository. To select an older ancestor boundary, add `--since v1.2.0`.

By default the boundary is the nearest reachable tag selected by `git describe --tags --abbrev=0 HEAD`, including lightweight and annotated tags. An unrelated branch's tag is ignored. Only non-merge commits after that tag are included, in Git's reverse traversal order. Without tags, all reachable commits are included. At the tagged release itself, all four sections say “No changes.” Shallow checkouts are rejected: fetch complete history first with `git fetch --unshallow` and fetch missing tags if necessary. The generator reads local history and never fetches automatically.

The categories are **Added**, **Fixed**, **Changed**, and **Removed**. Conventional `feat`/`feature`/`add` commits become Added; `fix`/`bugfix`/`revert` become Fixed; explicit removal types or subjects starting with remove/delete/drop become Removed. Other commits become Changed. Scopes and breaking-change `!` markers are supported; the original subject and a 12-character commit ID are retained. Ordinary “Add …”, “Fix …”, and “Remove …” subjects are also recognized. Classification is a documented heuristic, not semantic code analysis; review before publishing. Markdown metacharacters are escaped, and output contains no generation timestamp so identical history produces identical text.

The generator refuses to replace an existing file unless `--force` is supplied. It produces a complete Unreleased document; it does not merge or infer manually edited previous releases.

## Verification

Run `python -m unittest discover -s tests -v`. Tests create independent temporary Git repositories and cover release boundaries, four categories, missing tags, unrelated-branch tags, shallow history, escaping, and overwrite protection. `examples/CHANGELOG.md` is generated from this public GitHub repository before adding the implementation; `examples/README.md` pins its source commit and command.

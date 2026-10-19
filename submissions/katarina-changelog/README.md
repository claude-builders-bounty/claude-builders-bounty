# Git changelog generator

Requires Git, Bash and Python 3. No network access, credentials or third-party Python packages are used by the generator.

## Setup in three steps

1. Copy `changelog.sh` and `changelog.py` into your repository, keeping them together.
2. Ensure complete history: for a shallow clone run `git fetch --unshallow --tags`; otherwise run `git fetch --tags` when tags need refreshing.
3. Run `bash changelog.sh`. It writes `CHANGELOG.md` in the Git root.

Optional: `bash changelog.sh --repo /path/to/repo --output build/CHANGELOG.md`. Existing different output is replaced only with `--overwrite`; identical regeneration is a no-op.

The generator uses the nearest reachable tag from `git describe --tags --abbrev=0 HEAD`. It includes non-merge commits since that tag; without any reachable tag it includes all reachable history. Unreachable tags do not affect the range. It does not access a remote automatically or invent commit history from a shallow clone.

`feat`/`add` → Added; `fix`/`bugfix` → Fixed; `remove`/`delete` → Removed; everything else → Changed. Conventional Commit scopes are supported and `!` marks breaking changes. Free-form subjects remain Changed. Categorization is a deterministic heuristic, not semantic interpretation of the patch. Merge commits are excluded to avoid duplicate descriptions.

The date is the HEAD commit date, so unchanged history produces identical output. All four sections are included, with `None` when empty. Markdown/HTML in commit subjects is escaped.

Run verification: `python3 -m unittest discover -s . -p 'test_changelog.py' -v`. `SAMPLE.md` was generated from the real public bounty repository; it is not a synthetic fixture or a claim of maintainer acceptance.

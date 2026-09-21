# Generate a changelog

Local-only Git history processing. Requires Git and Python 3.8+; the wrapper also requires Bash. No packages, network calls, or AI service credentials.

## Setup in three steps

1. Copy this directory into your checkout.
2. Open a terminal in the checkout.
3. Run `bash generate-changelog/changelog.sh` (or `python generate-changelog/changelog.py` on Windows).

The default output is `CHANGELOG.md` in the current directory. Existing files are never overwritten. Use `--output CHANGELOG.next.md` to generate a separate file for review. Use `--repo /path/to/repo` to read another checkout; paths with spaces must be quoted. Set `PYTHON` to choose the wrapper's Python executable.

The base is Git's nearest reachable tag (`git describe --tags`), not the tag with the largest version or newest date. Untagged repositories use all history. Shallow repositories and empty repositories fail with a clear error. Merge commits are omitted, but the individual commits merged into the branch are included.

Conventional `feat` commits go under Added, `fix`/`bugfix`/`revert` under Fixed, and removal prefixes or removal verbs under Removed. Other commits go under Changed. Common leading verbs support non-conventional subjects; this is a deterministic heuristic, so review categorization before publishing. Conventional `!` markers are retained as BREAKING. Subjects are escaped for Markdown and HTML. Git is invoked with an argument list, never a shell command built from commit text.

Run checks with `python -m unittest discover -s generate-changelog/tests -v`. A sample from this real GitHub repository is included with its source revision in `SAMPLE-PROVENANCE.md`.

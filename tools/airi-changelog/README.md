# Generate a structured changelog

Local, deterministic Git history classification. Requires Git 2.30+ and Python 3.9+. No API, credentials, network calls, or package installation.

## Setup and use (3 steps)

1. Copy `changelog.py` and `changelog.sh` into your project, or keep them together in a tools directory.
2. Ensure a complete Git checkout with tags (`git fetch --unshallow --tags` only when the clone is shallow).
3. Run `bash /path/to/changelog.sh --repo . --output CHANGELOG.md` (or `python3 /path/to/changelog.py` on systems without Bash).

## Behavior

Uses the most recent reachable tag via `git describe --tags --abbrev=0 HEAD`; this means reachable ancestry, not the largest version number. Reads only commits after that tag. With no reachable tag, processes all history. Excludes merge commits to avoid repeating merged commits. No commits produces an explicit no-changes result.

Conventional commit `feat`/`add` → Added, `fix` → Fixed, `remove`/`removed` → Removed. Other conventional types → Changed. Untyped subjects beginning with add/introduce, fix/resolve/repair, or remove/delete/drop use the corresponding category. All other subjects → Changed. Breaking changes keep their category; this tool does not calculate version numbers. Classifications are rules, not semantic AI analysis: review before release.

Commit hashes provide traceability. HTML and Markdown syntax in subjects is escaped. Author names/emails and commit bodies are not exported. Existing files are preserved unless `--force` is passed; forced writes use atomic replacement. Output is a standalone generated Unreleased changelog, not an append operation to existing release history.

Optional: `--since v1.0.0`, `--repo /path/to/checkout`, `--output /path/to/output.md`, `--force`. Output paths are relative to the invoking working directory, not `--repo`.

## Validation

Run `python3 -m unittest -v test_changelog.py`. The tests create disposable repositories with real Git commands and exercise tagged history, no tags, null changes, Markdown escaping, malformed revisions, shallow history, and overwrite protection. A separate real GitHub repository sample is supplied in `SAMPLE_OUTPUT.md`.


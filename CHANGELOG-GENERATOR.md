# Generate a changelog

Requirements: Git, Python 3.9+, and Bash for the shell entry point (Git Bash works on Windows). No Python packages, credentials or network calls are needed.

## Setup and run (three steps)

1. Clone this repository, or copy `changelog.sh` and `generate_changelog.py` together into your project.
2. From your target Git repository, run `bash /path/to/changelog.sh` (or `bash changelog.sh` if copied there).
3. Review the generated `CHANGELOG.md` before publishing it.

Python-only equivalent: `python generate_changelog.py --repo /path/to/repo`.

If your Python executable has a custom location, set `PYTHON=/path/to/python` when invoking the Bash wrapper.

## Behavior

- The default base is Git's nearest reachable tag (`git describe --tags --abbrev=0`), including lightweight tags. It is not the highest semantic version or the most recently created tag anywhere in the repository.
- Only commits after that tag, reachable from the captured HEAD, are included. With no reachable tag, all reachable history is included. An empty/unborn repository returns an error.
- All four sections are emitted, including explicit empty sections. Commit hashes make every entry traceable. Merge commits are retained; entries are per commit, not deduplicated by message.
- Conventional `feat` becomes Added; `fix` becomes Fixed; `remove`, `removed`, and `delete` become Removed. Other types become Changed. Plain subjects beginning with Add/Added, Fix/Fixed, Remove/Removed/Delete/Deleted use the corresponding section. Everything else stays Changed.
- Classification is a transparent heuristic, not a claim to understand arbitrary prose. Original subjects (including breaking-change markers) are retained and Markdown/HTML escaped. Review body-only breaking changes separately.
- Existing output is protected unless `--force` is explicitly used. This generates a snapshot, not an incremental append to released history. Use `--output draft.md` for an existing project.
- No fetch is performed. Fetch missing tags/history yourself first; shallow clones can produce incomplete results.

Examples:

```bash
bash changelog.sh --repo ../project --output draft.md
bash changelog.sh --since v1.2.0 --output -
bash changelog.sh --force
python -m unittest discover -s tests -v
```

`--since` accepts an ancestor tag or commit. Unrelated or invalid revisions fail instead of silently widening the range. Output paths are relative to the current working directory. Generation only reads Git history; it does not modify commits or tags.

See `examples/README.md` for a reproducible run against a real public GitHub repository.

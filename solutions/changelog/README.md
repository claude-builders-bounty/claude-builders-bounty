# Git changelog generator

Submission candidate for issue #1. Requires Bash, Git, and Python 3.8+; no packages or API keys.

## Setup (two steps)

1. Copy this directory into your checkout or keep it in a separate tools directory.
2. From the repository you want to document, run `bash /path/to/changelog/changelog.sh`.

The output is `CHANGELOG.md` in the current directory. An existing file is protected;
use `--force` only if you want to replace it. This generates a fresh unreleased
section, rather than merging historical release sections into an existing changelog.

```bash
bash changelog.sh --repo /path/to/repo -o /tmp/CHANGELOG.md
bash changelog.sh --repo /path/to/repo -o -
python3 -m unittest discover -s tests -v
```

The most recent reachable tag is selected using `git describe --tags --abbrev=0`.
Both lightweight and annotated tags work. Commits reachable from HEAD but not
that tag are included, oldest first. With no reachable tags, all reachable
commits are included. Shallow checkouts can omit older tags/history: fetch the
full history and tags first if that matters. No network request is made.

Conventional `feat` commits become Added, `fix` becomes Fixed, and explicit
remove/delete/drop subjects become Removed. Other commits are Changed. Breaking
change markers and source hashes are retained. Plain-language add/fix/remove
subjects are recognized as a fallback. Unknown or ambiguous messages stay Changed;
categorization is heuristic and should be reviewed before release.

`sample-CHANGELOG.md` is actual output against this public repository at
`1aeae2a` (full hash and command in `VERIFICATION.md`).

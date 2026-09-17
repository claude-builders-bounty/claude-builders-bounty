# Git-history changelog generator

Python 3.10+, Git and Bash. No package installation, API key or model is needed.

## Setup and use

1. Copy this directory into a local Git checkout, or keep it outside the checkout.
2. Run `bash /path/to/changelog.sh --repo /path/to/project`.
3. Review `project/CHANGELOG.md` and commit it through your normal review process.

From this directory, `bash changelog.sh` uses the current checkout. `--stdout`
prints without writing. `--output PATH` writes to an explicit destination;
`--since TAG_OR_SHA` selects an ancestor boundary; `--all-history` ignores tags.
The program does not fetch remote history. A shallow clone produces an explicit
error: obtain complete history and tags before generating release notes.

## Decisions

The default boundary is Git's nearest reachable tag at HEAD, including lightweight
and annotated tags, not the lexicographically largest version from an unrelated
branch. The tag commit is excluded. Without a tag, all reachable non-merge commits
are included. Merge commit messages are skipped, but their constituent commits
remain. An empty repository yields four empty sections.

Conventional `feat`/`add` messages become Added, `fix`/`hotfix` become Fixed,
`remove`/`delete` become Removed, and all remaining commits become Changed.
Common imperative equivalents are supported. Scopes and breaking-change markers
are retained. Classification is a transparent heuristic, not semantic inference:
review ambiguous/revert subjects before publishing the notes.

The generated Unreleased section is marked. Re-running replaces only that block,
keeping previous releases and manual text outside it. Edits within the generated
block are intentionally regenerated. Existing files without a marked block are
preserved beneath a new section. Malformed markers fail without changing the file.
Writes are atomic and retain file mode. Concurrent content changes detected before
the replace produce an error; this is not a multi-writer locking protocol.

Commit text is rendered literally and is never executed. No network access,
repository mutation, implicit stage, commit or push occurs. To verify:

```sh
python3 -m unittest discover -s tests -v
```

`examples/` contains separately recorded output from an actual public GitHub
repository, with its origin, tag boundary, HEAD and reproduction command.

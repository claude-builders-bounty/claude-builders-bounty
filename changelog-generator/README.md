# Changelog generator (#1)

Requires Git, Bash and Python 3.8+ on your PATH. No packages, API keys or network
access are needed to generate a changelog from a local repository.

1. Copy `changelog.sh` and `changelog.py` together into your project, or keep this checkout.
2. Run `bash changelog.sh` in your project. From another directory, use
   `bash /path/to/changelog.sh --repo /path/to/project`.
3. Review the generated `CHANGELOG.md` at the target repository's root.

`--output release-notes.md` selects another file (relative to the repository root,
or an absolute path). Each run **replaces that file with a complete snapshot**;
it does not append to an existing release archive. Generation is atomic and
repeatable for unchanged history. Git commits, refs and tags are never modified.

The boundary is Git's nearest reachable tag (`git describe --tags --abbrev=0`),
including annotated and lightweight tags, rather than the highest version or an
unrelated branch's newest tag. The tagged commit is excluded. All later reachable
commits are included, including merge commits, oldest first within each section.
With no reachable tag, all history is used. An empty repository or HEAD exactly
at its tag produces four empty sections. Shallow history is rejected: obtain the
complete history and tags before running. The script never fetches automatically.

Classification uses the subject's leading word or Conventional Commit type:

| Section | Types / leading words |
| --- | --- |
| Added | feat, feature, add/adds/added, create/creates/created |
| Fixed | fix/fixes/fixed, bugfix, repair/repairs, resolve/resolves/resolved |
| Removed | remove/removes/removed, delete/deletes/deleted, drop/drops/dropped |
| Changed | Everything else, including refactors, docs, merges and reverts |

Scopes and breaking markers such as `feat(api)!:` are supported. Each commit gets
one section; its original subject and commit ID are retained. Bodies do not create
extra entries. This is a deterministic naming heuristic, not semantic analysis of
code changes: review ambiguous subjects. Subjects/tags are escaped as Markdown
text; no commit message is executed. Non-UTF-8 text uses replacement characters.
The generated file gets normal permissions (the existing file's mode when
replacing, otherwise `0666` minus your umask).

Run `python3 tests/test_changelog.py` from this directory to exercise the
**actual Bash entry point** against disposable Git repositories. The
[real-repository sample](samples/README.md) records a pinned MarkupSafe checkout,
real tag, output and reproduction command.

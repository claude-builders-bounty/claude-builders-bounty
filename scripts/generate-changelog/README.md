# Git changelog generator

A dependency-free Bash/Python submission candidate for
[bounty #1: Generate a structured CHANGELOG from git history](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1).
It reads commits after the nearest reachable Git tag and generates Markdown
grouped into **Added**, **Fixed**, **Changed**, and **Removed**.

## Setup and run: three steps

1. Install **Git**, **Python 3.9+**, and **Bash**, then extract this package.
2. From the package directory, run `python3 -m unittest -v test_changelog`.
3. Run `bash changelog.sh --repo /path/to/your/repository`.

This creates `CHANGELOG.md` in the target repository root. No package installation,
API key, account, LLM, or network request is needed. On Windows, use WSL or another
environment that supplies Bash and Python. Verification here was on Linux only.

## Examples

```bash
# Preview without writing anything.
bash changelog.sh --repo /path/to/repository --output -

# Choose an explicit exclusive start and inclusive end revision.
bash changelog.sh --repo /path/to/repository --since v1.0.0 --until HEAD --output -

# Choose a new output path relative to the target repository root.
bash changelog.sh --repo /path/to/repository --output CHANGELOG.next.md

# Explicitly replace an existing file after reviewing the preview.
bash changelog.sh --repo /path/to/repository --force

# Include merge commit messages as well as individual commits.
bash changelog.sh --repo /path/to/repository --include-merges --output -
```

`python3 changelog.py` accepts the same options. With no `--repo`, the current
working directory must be inside the target Git working tree. Paths containing
spaces must be quoted. The destination's parent directory must already exist.

## Range and categorization

By default, tag selection uses `git describe --tags --abbrev=0` against the resolved
end commit. Both annotated and lightweight tags are supported. "Nearest" is Git's
history-based selection, not the highest semantic version or most recently created
tag. Tags on unmerged branches do not affect the result. The base commit is excluded;
the end commit is included. Without a reachable tag, all reachable history is used.

Conventional subjects such as `feat(parser)!: add streaming` are categorized by
their type. `feat`, `feature`, `add`, and `added` map to Added; `fix`, `fixed`,
`bugfix`, and `hotfix` to Fixed; `remove`, `removed`, and `delete` to Removed.
Other types, including `refactor`, `docs`, `chore`, and `perf`, map to Changed.
Common imperative subjects such as `Add ...`, `Fix ...`, and `Remove ...` are
also recognized; other subjects fall back to Changed.

The original subject is preserved as escaped text, including scopes and breaking
change markers. Each entry includes a 12-character commit ID. Entries use
oldest-first topological order within each category. All four sections are emitted;
empty sections say `_No changes._`. Full boundary commit IDs are recorded for review.

## Safety and limits

- Git arguments are passed without a shell. Commit messages cannot execute commands.
- HTML and Markdown controls in commit subjects are escaped.
- Existing output is not overwritten unless `--force` is supplied. Publication is
  atomic; the default also protects against a competing writer creating the file.
- Output symlinks are rejected. Temporary files are removed if writing fails.
- Shallow repositories are rejected to avoid incomplete release notes. Fetch full
  history and tags yourself when appropriate; this tool never fetches from remotes.
- Empty repositories, invalid revisions, non-ancestor ranges, and unwritable output
  fail with a nonzero exit code and a readable error.
- Merge messages are excluded by default to avoid duplicate entries. Use
  `--include-merges` if a merge message describes a change absent from individual
  commit subjects.
- This generates one **Unreleased** section; it does not append to or preserve an
  existing changelog when `--force` is used. Review before replacing release history.
- Categorization is a transparent heuristic, not semantic analysis. Review release
  notes, especially breaking changes and reverts, before publishing.
- The implementation uses filesystem hard links for no-clobber output publication.
  Filesystems without hard-link support are not supported for that mode. stdout
  preview remains available.

## Verification and example

Run `python3 -m unittest -v test_changelog` and `bash -n changelog.sh`.
The 37 offline tests cover real temporary Git repositories, tag types and ancestry,
merges, revision boundaries, Unicode, escaped/untrusted input, shallow clones,
paths with spaces, overwrite protection, write races, and error cleanup.

[examples/CHANGELOG.md](examples/CHANGELOG.md) is actual generated output from the
public bounty repository. Its source and reproduction command are in
[examples/README.md](examples/README.md). See [EVIDENCE.md](EVIDENCE.md) for the
observed verification results.

Git reference: [git-describe](https://git-scm.com/docs/git-describe) and
[git-log](https://git-scm.com/docs/git-log).

## License

MIT; see [LICENSE](LICENSE).

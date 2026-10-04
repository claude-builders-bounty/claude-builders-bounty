# Git history changelog

Generate an unreleased `CHANGELOG.md` using local Git history. No API keys,
network calls, or Python packages are required.

## Setup and use

1. Install Git, Bash, and Python 3.9 or newer.
2. Copy this `changelog` directory anywhere on your machine.
3. Run the wrapper with your repository path:

   ```bash
   bash /path/to/changelog/changelog.sh --repo /path/to/project
   ```

The default repository is the current working directory. The default output is
`CHANGELOG.md` at the repository root. Run `bash changelog.sh --help` for options.
To keep an existing changelog, choose a new output file:

```bash
bash /path/to/changelog/changelog.sh --repo /path/to/project --output draft.md
```

Relative output paths are resolved from the current working directory. Existing
files and symlinks are rejected without modification. The destination directory
must exist. This generates a new snapshot; it does not update existing releases.

## History selection

The last tag is the nearest reachable tag selected by
`git describe --tags --abbrev=0 HEAD`, including lightweight and annotated tags.
It is not necessarily the greatest version number or the most recently dated tag.
The generator includes every commit in `tag..HEAD`, including merge commits,
exactly once by SHA. Entries within each category follow reverse topological
order. Different commits with the same subject remain separate entries.

Without a reachable tag, it includes all history reachable from HEAD. When HEAD
is tagged, all four categories contain `None.`. Empty repositories, non-repositories
and shallow clones fail explicitly. Use a complete local clone with the tags you
want considered; the script never fetches or changes Git refs or the index.

## Classification

Subjects are matched case-insensitively. Plain verbs are checked first, then
Conventional Commits with optional scopes and breaking-change markers (`!`).

| Category | Matching subject prefixes |
| --- | --- |
| Added | `feat:`, `feat(scope)!:`; plain `add`, `adds`, `added` |
| Fixed | `fix:`, `fix(scope)!:`; plain `fix`, `fixes`, `fixed` |
| Removed | `remove:`, `remove(scope)!:`; plain `remove`, `removes`, `removed` |
| Changed | Everything else, including docs, chore and refactor |

A plain verb must be followed by whitespace, a colon, or the end of the subject.
For example, `Added: export` is Added; `address parsing` is Changed.
Merge commits follow the same subject rules: `feat: integrate feature` is Added,
`remove old option` is Removed, and `Merge feature` is Changed.
This is deterministic categorization of messages, not semantic analysis of diffs.
Review ambiguous messages before publishing a release.

The output preserves subjects as escaped Markdown text and includes full commit
SHAs. The base and HEAD SHAs make the range auditable. Dates and release versions
are not invented. The same local refs and HEAD produce identical output bytes.

## Tests

From this repository's root:

```bash
python3 -m unittest discover -s changelog/tests -v
```

Tests create isolated temporary Git repositories. They cover classification,
range boundaries, annotated and lightweight tags, unreachable tags, merges,
Unicode, Markdown escaping, output preservation, determinism, and error cases.

## Real repository example

[Sample output](examples/CHANGELOG.md) was generated from
[pallets/itsdangerous](https://github.com/pallets/itsdangerous).

- HEAD: `672971d66a2ef9f85151e53283113f33d642dabd`
- Selected tag: `2.1.x`
- Base commit: `3ddb1ce418712d02f674a171b3f13ab20f6839a7`
- Included commits: 60 (1 Added, 1 Fixed, 53 Changed, 5 Removed)

To reproduce in a fresh directory (SSH access to GitHub is required):

```bash
git clone git@github.com:pallets/itsdangerous.git
git -C itsdangerous checkout --detach 672971d66a2ef9f85151e53283113f33d642dabd
bash /path/to/changelog/changelog.sh --repo itsdangerous --output sample.md
```

Compare `sample.md` with the committed example. Tag selection uses the tags
available in your clone; if upstream retags history, check the selected base SHA.

The upstream repository needs no dependency installation: the generator only
reads its Git history. The example output was written outside that clone.

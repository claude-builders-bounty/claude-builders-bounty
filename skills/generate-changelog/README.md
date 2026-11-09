# Generate a structured CHANGELOG

Zero-dependency Bash entry point for issue #1. Requires Git, Bash, and Python
3.9+; no API key, network call, package install, or LLM invocation is needed.

## Setup and run (3 steps)

1. Clone this repository, or copy the entire `skills/generate-changelog` directory.
2. Open a terminal in the Git project whose history you want to summarize.
3. Run `bash /path/to/generate-changelog/changelog.sh` to create `CHANGELOG.md`.

## Options

```bash
# Preview without writing a file.
bash /path/to/generate-changelog/changelog.sh --stdout

# Read another local repository and select an output path (relative to cwd).
bash /path/to/generate-changelog/changelog.sh --repo '/path/with spaces/project' --output release.md

# Choose an explicit starting reference, or explicitly replace an existing file.
bash /path/to/generate-changelog/changelog.sh --since v1.0.0 --output release.md --force
```

By default the script selects the nearest tag reachable from HEAD using
`git describe --tags --abbrev=0 HEAD` (annotated and lightweight tags). It reads
that tag's exclusive `tag..HEAD` range. With no reachable tag it includes the
entire available history. It reads local history only: fetch your tags/history
first, and use `git fetch --unshallow` if the clone is shallow. The script never
fetches or executes repository code, modifies Git state, or appends duplicate
release sections.

The generated document contains an `Unreleased` section, category headings for
nonempty groups, escaped commit subjects, and abbreviated commit IDs. Existing
files are refused unless `--force` is specified; forced replacement uses a
temporary file and atomic rename. This generates a release draft, rather than
merging into an existing historical changelog.

## Categorization

| Commit prefix | Section |
| --- | --- |
| `feat`, `add`, `added` | Added |
| `fix`, `fixed`, `bugfix` | Fixed |
| `remove`, `removed`, `delete` | Removed |
| Other prefixes and unrecognized subjects | Changed |

Conventional Commits scopes and `!` are supported, as are plain subjects such
as `Add export`. `!` or a `BREAKING CHANGE:` / `BREAKING-CHANGE:` body footer
adds a **BREAKING** marker. Every commit in the selected range is retained,
including merges and reverts (Changed). Squash/merge histories may therefore
contain similar subjects; this tool does not invent deduplication rules or
infer semantic changes from diffs. Review the generated draft before release.

## Verification

Run the entire test suite from the bounty repository root:

```bash
python3 -m unittest discover -s skills/generate-changelog/tests -v
bash -n skills/generate-changelog/changelog.sh
```

The integration tests create real temporary Git repositories; no mocks or
network are required. Covered cases include category/range correctness,
no tags, no new commits, an empty repository, an unreachable tag, Unicode and
breaking commits, paths with spaces, existing-file protection, forced output,
invalid references, and shell/Markdown input safety. Tested with Python 3.9.6
and 3.11.16.

A real public GitHub repository example and exact reproduction details are in
[examples/README.md](examples/README.md), with the checked-in
[Click CHANGELOG](examples/click-CHANGELOG.md).

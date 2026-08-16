# Git changelog generator

This small Bash tool creates a structured `CHANGELOG.md` from git history. It
looks for the latest reachable tag, reads the commits after that tag, and
groups commit subjects under `Added`, `Fixed`, `Changed`, or `Removed`.

## Setup in three steps

1. Copy `changelog.sh` into the repository whose history you want to inspect.
2. From that repository, run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md`, then commit it if it matches the project’s conventions.

The only dependency is Bash plus Git. If the repository has no tags, the tool
includes its complete history. A custom reference or output path is available
when needed:

```bash
bash changelog.sh --since v2.4.0 --output docs/CHANGELOG.md
bash changelog.sh --repo ../another-project
```

Commit subjects beginning with common prefixes such as `feat:`, `fix:`,
`remove:`, or `refactor:` are classified automatically. Unrecognised subjects
are kept under `Changed` so that no history is silently discarded.

The generated file is intentionally a reviewable starting point: maintainers
can edit wording, combine duplicate entries, and add release dates before
publishing.

## Verification

Run the dependency-free regression test from this directory:

```bash
bash test_changelog.sh
```

# Generate a changelog

A Python standard-library generator with a Bash entry point for turning Git history into a structured `CHANGELOG.md`. Requires Git, Python 3.10 or newer, and Bash.

## Setup and use — three steps

1. Copy the `bounty-1` directory into the target repository.
2. From the target repository, run `bash bounty-1/changelog.sh --repo "$PWD"` (add `--dry-run` to preview without writing).
3. Review and commit the generated `CHANGELOG.md`.

## Behavior

By default, the generator reads non-merge commits after the latest reachable tag. In an untagged repository it reads all commits. It understands Conventional Commit prefixes and falls back to keyword classification:

| Changelog section | Recognized examples |
| --- | --- |
| Added | `feat:`, `feature:`, `add:`, “introduce”, “create” |
| Fixed | `fix:`, `bugfix:`, `hotfix:`, “repair”, “resolve” |
| Removed | `remove:`, `delete:`, `deprecate:` |
| Changed | `docs:`, `refactor:`, `perf:`, `chore:`, uncategorized subjects, breaking changes |

Every generated section contains `Added`, `Fixed`, `Changed`, and `Removed` headings. Re-running the command replaces only the marked generated section and retains older manual changelog content.

## Options

```text
--repo PATH          Git repository path (default: current directory)
--output PATH        Output file (default: CHANGELOG.md)
--since REVISION     Start after this revision instead of the latest tag
--version LABEL      Heading label (default: Unreleased)
--date YYYY-MM-DD    Heading date (default: current UTC date)
--include-merges     Include merge commits
--dry-run            Print without writing
```

The Bash entry point forwards these options to the adjacent `changelog.py`, which invokes Git without a shell. Keep both files together when copying the directory. The original no-argument invocation and single positional output path are also supported; they read the current Git worktree and preserve existing manual changelog content.

# Generate Changelog

A zero-dependency Bash tool and Claude Code skill that turns Git history into a structured `CHANGELOG.md`.

## Setup (3 steps)

1. Copy `skills/generate-changelog` into `~/.claude/skills/generate-changelog`.
2. Run `chmod +x ~/.claude/skills/generate-changelog/changelog.sh`.
3. In Claude Code, run `/generate-changelog` (or run `bash ~/.claude/skills/generate-changelog/changelog.sh --repo "$PWD"`).

## Behavior

By default the script finds the latest tag reachable from `HEAD`, reads non-merge commits in `<tag>..HEAD`, and writes `CHANGELOG.md` in the target repository. If no tag exists, it uses the full history. Unknown commit styles are kept under `Changed`, so no commit is silently discarded.

| Commit subject | Section |
| --- | --- |
| `feat:`, `feature:`, `add:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `remove:`, `delete:`, `drop:`, `deprecate:`, `revert:` | Removed |
| `refactor:`, `perf:`, `docs:`, `chore:`, and everything else | Changed |

Scopes and breaking markers are supported, such as `feat(api)!: replace authentication`.

## Options

```text
--repo PATH       Git repository to inspect (default: current directory)
--output PATH     Output file, or - for stdout (default: CHANGELOG.md)
--since REV       Override the starting tag or revision
--version LABEL   Section label (default: Unreleased)
--force           Replace an existing output file
```

For safety, an existing output file is never replaced unless `--force` is supplied.

The committed real-repository example in `examples/pallets-click.md` records its source URL, latest tag, pinned HEAD, and reproduction command.

## Test

```bash
bash skills/generate-changelog/tests/test_changelog.sh
```

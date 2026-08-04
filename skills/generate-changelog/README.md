# Generate Changelog

Create a structured `CHANGELOG.md` from the current repository's git history.

## Setup

1. Copy `changelog.sh` into a git repository or keep it in this skill folder.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md` before committing it.

## Behavior

The script finds the most recent git tag and includes commits from that tag to
`HEAD`. If no tag exists, it includes the full history. Commit subjects are
grouped into `Added`, `Fixed`, `Changed`, and `Removed` using common commit
prefixes such as `feat:`, `fix:`, `remove:`, and `docs:`.

Use `--stdout` to preview without writing a file:

```bash
bash changelog.sh --stdout
```

Use `--output` to choose a custom path:

```bash
bash changelog.sh --output docs/CHANGELOG.md
```

Use `--repo`, `--since`, and `--version` when generating release notes from
outside the target repository or for a specific release:

```bash
bash changelog.sh --repo /path/to/repo --since v1.2.0 --version v1.3.0 --output docs/CHANGELOG.md
```

The `--since` value must be a git ref and cannot start with `-`, so malformed
values are rejected before they reach `git log`. Relative `--output` paths are
resolved inside the target repository and rejected if they escape it.

For Claude Code, the companion `SKILL.md` exposes the `/generate-changelog`
workflow and points back to this script.

# Generate Changelog

Dependency-free Claude Code skill and Bash command that writes a structured `CHANGELOG.md` from git history.

## Setup

1. Copy this directory into a git repository.
2. Run `bash generate-changelog/changelog.sh`.
3. Review the generated `CHANGELOG.md`.

## Behavior

- Uses commits since the latest reachable git tag.
- Falls back to the full repository history when no tag exists.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Preserves commit hashes in the output for reviewability.
- Writes deterministic Markdown so generated diffs are easy to audit.

## Claude Code Usage

Use the included `SKILL.md` as a project skill and ask:

```text
/generate-changelog
```

The skill runs the same Bash entrypoint.


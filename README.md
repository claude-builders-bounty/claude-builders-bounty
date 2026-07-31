# Generate Changelog

Create a structured `CHANGELOG.md` from Git history. Commits after the latest
reachable tag are grouped into Added, Fixed, Changed, and Removed using
conventional-commit types and common subject keywords.

## Setup and use

1. Copy `changelog.py` and `changelog.sh` into the root of the Git project.
2. Run `bash changelog.sh` (or `python3 changelog.py`) from that project.
3. Review the generated `CHANGELOG.md`, or pass `--version`, `--tag`, and `--output` as needed.

To enable the `/generate-changelog` command in Claude Code, copy
`.claude/skills/generate-changelog/SKILL.md` into the same path in your project.

## Examples

```bash
bash changelog.sh --version 1.2.0
bash changelog.sh --tag v1.1.0 --output docs/CHANGELOG.md
```

The generator skips merge commits, handles repositories without tags, and
writes the output atomically so an interrupted run does not leave a partial
file.

## Requirements

- Python 3.9+
- Git available on `PATH`

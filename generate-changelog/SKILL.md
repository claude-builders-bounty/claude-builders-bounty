# Generate Changelog

Use this skill when a user asks to generate or refresh a structured `CHANGELOG.md`
from a repository's git history.

## Workflow

1. Confirm you are inside the target git repository, then run `bash changelog.sh`.
2. Review the generated `CHANGELOG.md` sections for obvious categorization mistakes.
3. If needed, rerun with `--from <tag>` or `--output <file>` and summarize the exact range used.

## Behavior

- The script uses the latest reachable git tag as the default starting point.
- Commits are grouped into `Added`, `Fixed`, `Changed`, and `Removed`.
- Conventional prefixes such as `feat:`, `fix:`, `refactor:`, and `remove:` drive the categorization.
- Uncategorized commits are placed under `Changed` so nothing is dropped.

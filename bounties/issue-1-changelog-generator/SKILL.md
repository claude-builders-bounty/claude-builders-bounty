# Generate Changelog

Use this skill when a project needs a structured `CHANGELOG.md` generated from Git history.

## Workflow

1. Run `python generate_changelog.py --repo <project-path> --output <project-path>/CHANGELOG.md`.
2. Review the generated `Added`, `Fixed`, `Changed`, and `Removed` sections.
3. Commit the resulting `CHANGELOG.md` only after confirming the commit range is correct.

The generator uses commits since the most recent Git tag. If the repository has no tags, it uses all commits reachable from `HEAD`.

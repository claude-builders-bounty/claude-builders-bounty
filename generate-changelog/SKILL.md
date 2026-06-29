# Generate Changelog

Use this skill when the user asks to create, refresh, or audit a structured `CHANGELOG.md` from git history.

## Command

Run the repository command from the project root:

```bash
bash changelog.sh
```

Optional flags:

```bash
bash changelog.sh --output CHANGELOG.md
bash changelog.sh --range v1.2.0..HEAD
bash changelog.sh --include-authors
```

## Behavior

1. Detect the latest git tag with `git describe --tags --abbrev=0`.
2. Read commits from that tag to `HEAD`; if no tag exists, read the full history.
3. Ignore merge commits to keep the changelog focused on authored changes.
4. Categorize each commit into `Added`, `Fixed`, `Changed`, or `Removed`.
5. Write a Keep a Changelog-style `CHANGELOG.md` with the generation date and source range.

## Categorization Rules

- `Added`: `feat`, `feature`, `add`, `create`, `implement`, `introduce`, or matching keywords.
- `Fixed`: `fix`, `bugfix`, `hotfix`, `repair`, `resolve`, `correct`, or bug/regression keywords.
- `Removed`: `remove`, `delete`, `drop`, `deprecate`, or matching keywords.
- `Changed`: `change`, `refactor`, `perf`, `docs`, `style`, `test`, `build`, `ci`, `chore`, `update`, `improve`, or anything that does not clearly fit another bucket.

## Quality Checklist

Before returning the changelog to the user:

- Confirm the command ran inside a git repository.
- Confirm the script used the latest tag when one exists.
- Confirm every section is valid Markdown.
- Mention if there were no tags and the full history was used.

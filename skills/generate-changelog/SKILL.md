# Generate Changelog From Git History

Use this skill when the user asks to create or refresh a structured `CHANGELOG.md` from the current repository history.

## Command

Run:

```bash
bash skills/generate-changelog/changelog.sh
```

Optional arguments:

```bash
bash skills/generate-changelog/changelog.sh --output CHANGELOG.md --version vNext
```

## Behavior

The command finds commits since the latest Git tag, categorizes them into `Added`, `Fixed`, `Changed`, and `Removed`, then writes a Markdown changelog section. If the repository has no tags, it uses the first commit as the start of history.

## Review Checklist

- Confirm the command ran inside the intended Git repository.
- Review commit grouping for any ambiguous commit messages.
- Edit the generated prose before release if the repository uses a stricter changelog style.

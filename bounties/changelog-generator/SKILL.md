# Generate Changelog

Use this skill when a user asks to generate or refresh a `CHANGELOG.md` from git history.

## Command

Run the bundled script from the target repository:

```bash
bash changelog.sh
```

If the script is stored outside the target repository, pass the repository path:

```bash
bash changelog.sh --repo /path/to/project --output CHANGELOG.md
```

## Behavior

The script:

- finds the most recent git tag with `git describe --tags --abbrev=0`
- reads commits since that tag, or all commits when no tag exists
- groups entries into `Added`, `Fixed`, `Changed`, and `Removed`
- writes a Keep a Changelog-style `CHANGELOG.md`
- keeps existing changelog content below the newly generated section when possible

## Review Checklist

- Confirm the target directory is a git repository.
- Review the generated categories before committing.
- If a project uses non-standard commit messages, manually adjust any entry that landed in `Changed`.


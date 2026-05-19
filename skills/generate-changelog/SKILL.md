# Generate Changelog

Use this skill when the user asks to create, refresh, or inspect a `CHANGELOG.md`
from the current repository's git history.

## Command

Run the repository script from the project root:

```bash
bash changelog.sh
```

## Behavior

- Detects the latest reachable git tag with `git describe --tags --abbrev=0`.
- Reads commits from that tag through `HEAD`; if no tag exists, reads all commits.
- Categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a complete `CHANGELOG.md` with the source range and generation date.

## Options

```bash
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md --version 1.2.3
bash changelog.sh --from v1.0.0 --to HEAD
```

Before committing the generated changelog, inspect the diff and adjust wording if
the commit subjects are too terse for release notes.

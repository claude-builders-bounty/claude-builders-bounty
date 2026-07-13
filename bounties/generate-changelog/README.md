# Generate changelog from git history

This bounty deliverable adds `changelog.sh`, a small Bash CLI that generates a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup in 3 steps

```bash
chmod +x changelog.sh
./changelog.sh
cat CHANGELOG.md
```

## Behavior

- Finds the latest tag with `git describe --tags --abbrev=0`
- Reads commits since that tag, or all commits if no tag exists
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`
- Writes a Keep-a-Changelog-style `CHANGELOG.md`
- Includes commit short SHAs for traceability

## Categorization

| Category | Commit prefixes / keywords |
| --- | --- |
| Added | `feat`, `add`, `create`, `implement` |
| Fixed | `fix`, `bug`, `patch`, `repair`, `resolve` |
| Removed | `remove`, `delete`, `drop`, `deprecate` |
| Changed | everything else, including `refactor`, `docs`, `chore`, `test` |

## Sample

See `sample-output.md`, generated from this repository's current git history.

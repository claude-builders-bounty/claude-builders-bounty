# Generate Changelog

Create a structured `CHANGELOG.md` from git history since the latest tag.

## Setup

```bash
chmod +x tools/generate-changelog/changelog.sh
./tools/generate-changelog/changelog.sh
git diff -- CHANGELOG.md
```

## How It Works

The script finds the latest reachable git tag with `git describe --tags --abbrev=0`. If no tag exists, it uses the full repository history. Commit subjects are categorized into:

- `Added`: `feat`, `add`, `create`, `implement`
- `Fixed`: `fix`, `bug`, `patch`, `repair`
- `Removed`: `remove`, `delete`, `drop`
- `Changed`: everything else, including `chore`, `docs`, `refactor`, and `update`

The generated file includes the source commit range and a UTC generation timestamp so release notes can be reproduced.

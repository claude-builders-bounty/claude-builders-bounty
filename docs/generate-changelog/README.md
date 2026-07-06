# Generate a structured changelog

This tool creates a `CHANGELOG.md` from commits since the latest reachable git
tag. It works through `bash changelog.sh` and does not require external APIs.

## Setup

1. Copy `changelog.sh` and `scripts/generate_changelog.py` into your repository.
2. Run `chmod +x changelog.sh`.
3. Run `bash changelog.sh`.

## Usage

```bash
bash changelog.sh
bash changelog.sh --version v1.4.0
bash changelog.sh --from-ref v1.3.0 --output docs/CHANGELOG.md
bash changelog.sh --dry-run
```

The script:

- Finds the latest git tag with `git describe --tags --abbrev=0`.
- Reads non-merge commits after that tag.
- Auto-categorizes entries into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a properly formatted `CHANGELOG.md`.

Conventional commit prefixes are handled directly:

- `feat:` -> `Added`
- `fix:` -> `Fixed`
- `remove:` / `delete:` -> `Removed`
- `docs:`, `refactor:`, `chore:`, `ci:`, and other maintenance commits -> `Changed`

If a repository has no tags, the script uses the full git history and states
that in the generated output.

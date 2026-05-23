# Generate Changelog

Generate a structured `CHANGELOG.md` from commits since the last git tag.

## Setup

1. Copy `generate_changelog.py` into a git repository.
2. Run `python generate_changelog.py --output CHANGELOG.md`.
3. Review the generated `Added`, `Fixed`, `Changed`, and `Removed` sections before committing.

## Usage

```bash
python generate_changelog.py
python generate_changelog.py --repo /path/to/repo --output CHANGELOG.md
python generate_changelog.py --since v1.2.0 --version v1.3.0
python generate_changelog.py --dry-run
```

By default, the script:

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Reads commits after that tag.
- Preserves commit order from oldest to newest.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Keep a Changelog-style `CHANGELOG.md`.

If a repository has no tags, the script uses the full commit history.

## Claude Code Skill

`SKILL.md` contains the same workflow as a native Claude Code skill. Use it when you want Claude Code to generate or refresh a changelog inside an existing repository.

## Sample Output

See `samples/CHANGELOG.sample.md` for output generated from real GitHub commit messages from `fastapi/full-stack-fastapi-template`.

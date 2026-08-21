# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from commits since the latest Git tag. Commits are grouped into **Added**, **Fixed**, **Changed**, and **Removed** using Conventional Commit prefixes plus conservative verb fallbacks.

## Setup in three steps

1. Copy `generate_changelog.py` into your project (optionally copy `SKILL.md` into `.claude/skills/generate-changelog/`).
2. Run `python3 generate_changelog.py --repo .`.
3. Review and commit the generated `CHANGELOG.md`.

Preview without writing:

```bash
python3 generate_changelog.py --repo . --stdout
```

## Behavior

- Finds the latest reachable Git tag with `git describe`.
- Reads non-merge commits from `<tag>..HEAD`; if no tag exists, reads all commits.
- Supports Conventional Commits, scopes, and breaking `!` markers.
- Includes short commit SHAs for traceability.
- Uses only Python's standard library and local Git; no API key or network access.

## Test

```bash
python3 -m unittest -v test_generate_changelog.py
```

The integration test creates a temporary real Git repository, tags a release, adds a new commit, and verifies that only the post-tag commit is included.

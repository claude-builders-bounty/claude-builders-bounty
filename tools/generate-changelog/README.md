# Generate Changelog

Dependency-free Python CLI that creates a structured `CHANGELOG.md` from git history.

## Setup In 3 Steps

```bash
cd your-repo
python3 /path/to/generate_changelog.py --output CHANGELOG.md
git diff -- CHANGELOG.md
```

## Usage

```bash
python3 tools/generate-changelog/generate_changelog.py
```

The script finds the latest git tag with `git describe --tags --abbrev=0`, reads commits from that tag to `HEAD`, and writes a Markdown changelog grouped by:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

Use `--since <tag-or-ref>` to choose the starting point manually.

```bash
python3 tools/generate-changelog/generate_changelog.py --since v1.2.0
```

Use `--stdout` to preview without writing a file.

```bash
python3 tools/generate-changelog/generate_changelog.py --stdout
```

## Categorization Rules

- Commit subjects beginning with `feat`, `add`, or `create` go to `Added`.
- Commit subjects beginning with `fix`, `bug`, or `bugfix` go to `Fixed`.
- Commit subjects beginning with `remove` or `delete` go to `Removed`.
- Everything else goes to `Changed`.

Conventional commit prefixes such as `feat(api):` and `fix(ui):` are supported.

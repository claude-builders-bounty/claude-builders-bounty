# CHANGELOG Generator

Utility to generate a structured CHANGELOG from the git history of a repository.

## Features
- Parses `git log` and produces a markdown changelog grouped by version tags (if present) or by date.
- Supports custom templates via a simple Jinja‑like placeholder system.
- Zero‑dependency (uses only the standard library) or optional `GitPython` for richer metadata.

## Usage
```bash
python3 generate_changelog.py [--output CHANGELOG.md] [--template TEMPLATE.md]
```
- `--output` – file to write the changelog (default: `CHANGELOG.md`).
- `--template` – optional markdown template with placeholders `{entries}`.

The script will:
1. Detect the repository root.
2. Collect commits since the last tag (or all commits if no tags).
3. Group commits by type (feat, fix, docs, refactor, perf, test, chore) using conventional‑commit prefixes.
4. Render a tidy markdown file.

## Example Output
```markdown
# Changelog

## v1.2.0 – 2026-03-20
- **feat:** add support for custom templates
- **fix:** correct date parsing bug

## v1.1.0 – 2026-02-10
- **docs:** update README with usage examples
```

## License
MIT – feel free to adapt and reuse.

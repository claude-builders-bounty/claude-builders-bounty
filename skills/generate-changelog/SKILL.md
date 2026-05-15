# Generate Changelog

Generate a structured `CHANGELOG.md` from a repository's git history.

## Usage

Run this from the target repository root:

```bash
bash scripts/changelog.sh
```

The script finds commits since the latest git tag. If no tag exists, it uses the full git history. It writes a Keep a Changelog-style `CHANGELOG.md` with `Added`, `Fixed`, `Changed`, and `Removed` sections.

## Options

```bash
bash scripts/changelog.sh --output docs/CHANGELOG.md
bash scripts/changelog.sh --since v1.2.0
```

## Review Checklist

- Confirm the generated range is correct.
- Skim each category for any commit subjects that should be reworded.
- Commit both the script and the generated changelog when the output is acceptable.

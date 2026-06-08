# Changelog Generator Skill

Submission for bounty [#1](../../../issues/1).

This skill generates a structured `CHANGELOG.md` from git history. It is dependency-free and groups commits by Conventional Commit-style prefixes.

## Usage

```bash
python skills/changelog-generator/generate_changelog.py --output CHANGELOG.md
```

Generate changes since a tag:

```bash
python skills/changelog-generator/generate_changelog.py --since v1.2.0 --output CHANGELOG.md
```

Limit commit count:

```bash
python skills/changelog-generator/generate_changelog.py --max-count 25
```

## Test

```bash
python -m pytest
```

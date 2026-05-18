# Generate CHANGELOG

Generate a structured `CHANGELOG.md` from git history, with auto-categorization.

## Usage

````markdown
/generate-changelog
````

Or run directly:

```bash
python skills/generate-changelog/changelog.py
python skills/generate-changelog/changelog.py --stdout
python skills/generate-changelog/changelog.py --since v1.0.0
```

## What It Does

1. Fetches all commits since the last git tag
2. Auto-categorizes into **Added** / **Fixed** / **Changed** / **Removed**
3. Writes a clean `CHANGELOG.md` to the project root

Categorization uses [Conventional Commits](https://www.conventionalcommits.org/) prefixes (`feat:`, `fix:`, `refactor:`, etc.) with keyword fallback — no GitHub Actions or external dependencies required.

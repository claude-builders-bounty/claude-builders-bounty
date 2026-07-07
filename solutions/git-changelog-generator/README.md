# Git CHANGELOG Generator

An automated script that generates a structured `CHANGELOG.md` from the project's git history since the last release tag.

## Features

- **Automated Tag Parsing**: Discovers the latest git tag automatically and filters commits from `<tag>..HEAD`.
- **Intelligent Classification**: Groups commit messages by convention (`feat:` -> `Added`, `fix:` -> `Fixed`, `remove:` -> `Removed`, other -> `Changed`).
- **Markdown Formatting**: Outputs a clean, standard changelog.

---

## Usage

### 1. Run the script
Run the script from the root of any git repository:

```bash
bash solutions/git-changelog-generator/changelog.sh
```

This will analyze the git history and output a `CHANGELOG.md` file in the current directory.

---

## Running Tests

To run the unit tests:

```bash
python -m unittest solutions/git-changelog-generator/test_changelog.py
```

# generate-changelog

Fast, automated git changelog generator following the **Keep a Changelog** standard and Conventional Commits / keyword semantics.

Automatically parses commits since the last git tag, categorizes changes into **Added**, **Fixed**, **Changed**, and **Removed**, and formats them neatly into `CHANGELOG.md`.

## Features
- **Semantic Categorization**: Supports Conventional Commits (`feat:`, `fix:`, `perf:`, `refactor:`, `deprecate:`, etc.) and natural commit verbs (`add ...`, `fixed ...`, `remove ...`).
- **Tag Auto-Detection**: Discovers commits since the last reachable git tag automatically (via `git describe`).
- **Clean Markdown Output**: Produces Keep a Changelog compliant markdown with commit hashes and proper headings.
- **Merge Commit Filtering**: Automatically filters out git merge commits to keep changelogs clean.
- **Zero External Dependencies**: Standard library Python 3 only.

---

## Installation & Quickstart (≤ 3 steps)

1. **Clone or copy the tool:**
   ```bash
   git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
   cd claude-builders-bounty
   ```
2. **Make the script executable:**
   ```bash
   chmod +x changelog.sh generate_changelog.py
   ```
3. **Generate your changelog:**
   ```bash
   ./changelog.sh
   # Or directly via Python:
   python3 generate_changelog.py
   ```

---

## Usage

```bash
# Run in the current git repository (outputs to CHANGELOG.md)
./changelog.sh

# Run against a specific repository
./changelog.sh --repo /path/to/repo --output CHANGELOG.md

# Specify custom release tag or version title
./changelog.sh --tag v1.0.0

# Generate changelog for a specific tag or commit range
./changelog.sh --since v1.4.1 --tag v1.5.0
```

### Options
- `--repo`: Path to the git repository (default: `.`)
- `--output`, `-o`: Path to output file (default: `CHANGELOG.md`)
- `--tag`, `-t`: Tag / release version label for the changelog header (default: `Unreleased`)
- `--since`, `-s`: Git tag or revision to start from (default: latest git tag)

---

## Testing

Run the automated test suite:
```bash
python3 test_changelog.py
```
Suite contains unit tests, edge case tests (no tags, empty repos, merge commit filtering), and end-to-end git integration tests.

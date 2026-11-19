# Generate CHANGELOG Skill 📝

Automatically generate a structured, Keep-a-Changelog compliant `CHANGELOG.md` from your repository's git history.

## Features

- 🏷️ **Tag-aware**: Automatically detects commits since the last git tag (or from repository origin if no tags exist).
- 📂 **Auto-categorization**: Sorts commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- 🔀 **Conventional Commits & Imperative Verbs**: Accurately handles `feat:`, `fix:`, `docs:`, `refactor:`, `perf:`, `chore:`, `remove:`, as well as standard Git verbs (`Add`, `Fix`, `Update`, `Remove`).
- 🔄 **Incremental Updates**: Seamlessly prepends new release sections into an existing `CHANGELOG.md` without overwriting historical notes.
- ⚡ **Flexible Execution**: Use as a Claude Code skill (`/generate-changelog`), via `bash changelog.sh`, or `python generate_changelog.py`.

---

## Quickstart (3 Steps)

### Step 1: Copy skill to your repository
```bash
cp -r skills/generate-changelog path/to/your/repo/
```

### Step 2: Run the generator
From your repository root:
```bash
python3 skills/generate-changelog/generate_changelog.py
```
*(or run `bash skills/generate-changelog/changelog.sh`)*

### Step 3: Review your `CHANGELOG.md`
Check the generated `CHANGELOG.md` and commit it:
```bash
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG.md"
```

---

## Sample Generated Output

Tested on `claude-builders-bounty` repository:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Initial Release] - 2026-11-19

### Added
- Hook: add pre-tool-use destructive bash and SQL blocker ([`afdc49d`])
- Initial README with bounty board ([`1aeae2a`])

### Fixed
- Honor Claude hook payload and blocking protocol ([`fdbd0d4`])

### Changed
- Docs: add 2-command installation instructions for security hook ([`a851940`])
```

---

## Running Unit Tests

```bash
python -m unittest discover -s skills/generate-changelog -p "test_*.py"
```

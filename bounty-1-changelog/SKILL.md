# generate-changelog

Generate a structured CHANGELOG.md from git commit history, auto-categorized by commit type.

## Usage

```
/generate-changelog
/generate-changelog --all
/generate-changelog --since v2.0.0
```

## What It Does

1. Reads the git log since the most recent tag (or a specified reference).
2. Categorizes each commit into **Added**, **Fixed**, **Changed**, or **Removed**.
3. Outputs a clean, Keep-a-Changelog-compliant `CHANGELOG.md`.

## Categorization Rules

Commits are classified using two strategies, applied in order:

### 1. Conventional Commit Prefixes

| Prefix | Section |
|---|---|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:`, `perf:`, `style:`, `docs:`, `build:`, `ci:`, `chore:`, `test:` | Changed |
| `remove:`, `deprecate:` | Removed |

### 2. Keyword Fallback

If no conventional prefix is detected, the first word of the message is matched:

| Keywords | Section |
|---|---|
| add, create, new, implement, introduce | Added |
| fix, bug, bugfix, patch, resolve, hotfix | Fixed |
| update, change, modify, refactor, improve, upgrade, rename, move, migrate | Changed |
| remove, delete, drop, deprecate | Removed |

Unmatched commits default to **Changed**.

## Flags

| Flag | Description |
|---|---|
| `--all` | Generate changelog across all tags, not just since the latest |
| `--since <ref>` | Generate from a specific tag or commit |
| `--output <file>` | Write to a custom file (default: `CHANGELOG.md`) |
| `--dry-run` | Print to stdout instead of writing a file |

## Instructions for Claude

When the user runs `/generate-changelog`, execute the following steps:

1. **Locate the script.** Find `changelog.sh` in this skill directory.
2. **Run it.** Execute `bash changelog.sh` with any flags the user provided. Pass `--all` if the user asks for a full changelog. Pass `--dry-run` first if you want to preview.
3. **Review the output.** Read the generated `CHANGELOG.md` and present a summary to the user.
4. **Handle edge cases:**
   - If the repository has no tags, the script generates an "Unreleased" section with all commits.
   - If there are no new commits since the last tag, inform the user that the changelog is already up to date.
   - Merge commits are automatically excluded.
5. **Prepend to existing file.** If a `CHANGELOG.md` already exists in the repo root, read it first, then prepend the new section below the file header (lines starting with `# Changelog` and the description paragraph). Do not duplicate existing sections.

Do not modify commit messages. Do not invent entries. Every line in the output must correspond to an actual git commit.

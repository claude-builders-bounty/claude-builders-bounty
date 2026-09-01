# SKILL: Generate Structured CHANGELOG from Git History

## Description

This skill generates a structured `CHANGELOG.md` file from a project's git history.
It parses conventional commit messages and auto-categorizes them into
**Added**, **Fixed**, **Changed**, and **Removed** sections following the
[Keep a Changelog](https://keepachangelog.com/) format.

## Trigger

Use this skill when the user asks to:
- Generate a changelog
- Create a CHANGELOG.md
- Summarize recent git commits
- Produce release notes from git history

## Instructions

When this skill is invoked, follow these steps:

### 1. Locate the changelog script

The script `changelog.sh` lives in the same directory as this `SKILL.md` file.

### 2. Run the script

Execute the script in the project's root directory:

```bash
bash <skill_dir>/changelog.sh --repo <project_path> --output CHANGELOG.md
```

Options:
- `--from <tag>` — Start from a specific git tag (default: last reachable tag)
- `--to <ref>` — End at a specific ref (default: HEAD)
- `--output <file>` — Output file path (default: CHANGELOG.md)
- `--repo <path>` — Path to git repository (default: current directory)

### 3. Review and present the output

After the script runs:
1. Read the generated `CHANGELOG.md` file
2. Present a summary to the user showing:
   - Number of commits parsed
   - Breakdown by category (Added / Fixed / Changed / Removed)
   - The version label used
3. Ask the user if they want to modify any entries or regenerate with different options

### Supported Commit Types

The script recognizes [Conventional Commits](https://www.conventionalcommits.org/)
format: `type(scope): description`

| Commit Type      | Category  |
|------------------|-----------|
| `feat` / `feature` / `add` | Added    |
| `fix` / `bugfix` / `hotfix` | Fixed    |
| `refactor` / `perf` / `chore` / `docs` / `style` / `ci` / `build` | Changed  |
| `remove` / `revert` / `deprecate` | Removed  |

Commits with `!` after the type (e.g., `feat!:`) are marked with ⚠️ BREAKING.

Non-conventional commit messages are placed in the **Changed** category.

### Example

```bash
# Generate changelog for the current repo
bash changelog.sh

# Generate from v1.0.0 to v2.0.0
bash changelog.sh --from v1.0.0 --to v2.0.0 --output docs/CHANGELOG.md
```

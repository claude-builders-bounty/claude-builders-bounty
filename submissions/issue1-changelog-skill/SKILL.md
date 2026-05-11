# generate-changelog

Generate a structured `CHANGELOG.md` from your git history since the last tag.

## Usage

```
/generate-changelog
```

## What it does

1. Finds the most recent git tag (or uses all commits if no tags exist)
2. Reads every commit since that tag
3. Auto-categorizes into **Added / Fixed / Changed / Removed / Other**
4. Writes a formatted `CHANGELOG.md` in the current directory

## Steps

Run this in your project root:

```bash
bash changelog.sh
```

Or with options:

```bash
bash changelog.sh --since v1.2.3          # explicit start tag
bash changelog.sh --output RELEASES.md    # custom output file
```

## Categorization rules

| Commit prefix | Section |
|---------------|---------|
| `feat`, `add`, `new` | Added |
| `fix`, `bug`, `patch`, `hotfix` | Fixed |
| `refactor`, `perf`, `style`, `chore`, `update`, `change`, `improve` | Changed |
| `revert`, `remove`, `delete`, `drop` | Removed |
| anything else | Other |

## Setup

```bash
# Step 1: Copy to your project
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/submissions/issue1-changelog-skill/changelog.sh

# Step 2: Make executable
chmod +x changelog.sh

# Step 3: Run
bash changelog.sh
```

# generate-changelog

A Claude Code skill and standalone bash script that generates a structured `CHANGELOG.md` from git history. Commits are auto-categorized into **Added**, **Fixed**, **Changed**, and **Removed** sections following the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

## Setup (3 steps)

### 1. Copy the skill into your project

```bash
cp SKILL.md /path/to/your-repo/.claude/skills/generate-changelog.md
```

Or, to use the standalone bash script instead:

```bash
cp changelog.sh /path/to/your-repo/
```

### 2. Run it

**As a Claude Code skill:**

```
/generate-changelog
```

**As a bash script:**

```bash
bash changelog.sh
```

### 3. Review the output

Open `CHANGELOG.md` in your repo root. Commits are grouped by category with short hashes for traceability.

## How it works

1. Finds the latest git tag. If none exists, uses the full commit history.
2. Reads all non-merge commits since that tag.
3. Categorizes each commit by its conventional commit prefix or keywords:

   | Section     | Triggers                                                        |
   |-------------|-----------------------------------------------------------------|
   | **Added**   | `feat:`, `add:`, or keywords: add, new, create, implement, introduce, support |
   | **Fixed**   | `fix:`, `bugfix:`, or keywords: fix, bug, patch, resolve, correct, repair    |
   | **Changed** | `refactor:`, `chore:`, `docs:`, `perf:`, etc., or keywords: update, improve, enhance |
   | **Removed** | `revert:`, or keywords: remove, delete, deprecate, drop, cleanup             |

4. Strips conventional commit prefixes for cleaner output.
5. Writes a properly formatted `CHANGELOG.md`.

## Options (bash script)

```
bash changelog.sh [OPTIONS]

  -v, --version VERSION   Set the version header (default: auto-detect)
  -o, --output FILE       Output file (default: CHANGELOG.md)
  -r, --range RANGE       Git log range (default: last tag..HEAD)
  -a, --append            Preserve existing CHANGELOG entries
  -h, --help              Show help
```

## Example

```bash
# Generate changelog for everything since the last tag
bash changelog.sh

# Generate a specific version
bash changelog.sh -v 2.1.0

# Append to existing CHANGELOG.md
bash changelog.sh -v 2.1.0 --append
```

## Sample output

See [SAMPLE_OUTPUT.md](./SAMPLE_OUTPUT.md) for a real-world example generated from this repository.

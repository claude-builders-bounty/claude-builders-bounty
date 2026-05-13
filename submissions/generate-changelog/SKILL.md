---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, auto-categorizing commits into Added/Fixed/Changed/Removed sections
---

# Generate Changelog

When the user invokes `/generate-changelog`, generate a structured `CHANGELOG.md` from the project's git history.

## Steps

1. **Find the last tag** to determine the range of commits:
   ```bash
   git describe --tags --abbrev=0 2>/dev/null
   ```
   If no tag exists, include all commits.

2. **Collect commits** since the last tag:
   ```bash
   git log <tag>..HEAD --pretty=format:"%s" --no-merges
   ```

3. **Categorize each commit** into one of four sections based on its prefix or keywords:

   | Category | Conventional Commit Prefixes | Keyword Fallbacks |
   |----------|------------------------------|-------------------|
   | **Added** | `feat:`, `add:`, `new:`, `create:`, `implement:` | "add", "new", "create", "implement", "introduce" |
   | **Fixed** | `fix:`, `bug:`, `patch:`, `resolve:` | "fix", "bug", "patch", "resolve", "repair" |
   | **Changed** | `refactor:`, `update:`, `chore:`, `perf:`, `style:`, `ci:`, `build:`, `docs:`, `test:` | Everything else |
   | **Removed** | `remove:`, `delete:`, `drop:`, `deprecate:` | "remove", "delete", "drop", "deprecate" |

4. **Write CHANGELOG.md** in [Keep a Changelog](https://keepachangelog.com/) format:

   ```markdown
   # Changelog

   ## [<version>] - <YYYY-MM-DD>

   ### Added
   - <commit message>

   ### Fixed
   - <commit message>

   ### Changed
   - <commit message>

   ### Removed
   - <commit message>
   ```

5. **Report** the number of commits categorized and the output file path.

## Usage

Alternatively, run the bash script directly:
```bash
bash changelog.sh                    # Generate from last tag
bash changelog.sh --since v1.0.0     # Generate since specific tag
bash changelog.sh --output CHANGES   # Custom output filename
```

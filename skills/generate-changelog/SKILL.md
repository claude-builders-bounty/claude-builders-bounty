# generate-changelog

Generates a structured CHANGELOG.md from git history, auto-categorizing commits into Added, Fixed, Changed, and Removed sections.

## Instructions

When the user invokes `/generate-changelog`, follow these steps:

1. **Determine the commit range.** Run `git describe --tags --abbrev=0 2>/dev/null` to find the latest tag. If a tag exists, use commits since that tag (`<tag>..HEAD`). If no tags exist, use all commits on the current branch.

2. **Fetch the commit log.** Run the appropriate git log command:
   ```
   git log <range> --pretty=format:"%H %s" --no-merges
   ```

3. **Categorize each commit** by its subject line into one of these sections:
   - **Added**: commits starting with `feat:`, `feat(`, `add:`, `add(`, or containing "add", "new", "create", "implement", "introduce", "support" (case-insensitive)
   - **Fixed**: commits starting with `fix:`, `fix(`, `bugfix:`, or containing "fix", "bug", "patch", "resolve", "correct", "repair" (case-insensitive)
   - **Changed**: commits starting with `refactor:`, `perf:`, `style:`, `chore:`, `build:`, `ci:`, `docs:`, `test:`, or containing "update", "change", "modify", "improve", "enhance", "refactor", "rename", "move", "migrate", "upgrade", "bump" (case-insensitive)
   - **Removed**: commits starting with `revert:` or containing "remove", "delete", "deprecate", "drop", "clean up", "cleanup" (case-insensitive)
   - If a commit does not match any category, place it under **Changed** as the default.
   - A commit should appear in only one section. Use the first match in the order: Fixed > Added > Removed > Changed.

4. **Determine the version header.** If the user specifies a version, use it. Otherwise:
   - If a latest tag exists, use `[Unreleased]` as the header.
   - If no tags exist, use `[1.0.0]` as the header.

5. **Generate the CHANGELOG.md** with this format:
   ```markdown
   # Changelog

   All notable changes to this project will be documented in this file.

   The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

   ## [Version] - YYYY-MM-DD

   ### Added
   - Commit message here (short hash)

   ### Fixed
   - Commit message here (short hash)

   ### Changed
   - Commit message here (short hash)

   ### Removed
   - Commit message here (short hash)
   ```

   Rules:
   - Use today's date in YYYY-MM-DD format.
   - Include the short hash (first 7 chars) in parentheses after each message.
   - Strip conventional commit prefixes (e.g., `feat: ` or `fix(scope): `) from the displayed message for cleaner output.
   - Omit any section that has zero entries.
   - If a CHANGELOG.md already exists, prepend the new version section after the header (preserve existing entries).

6. **Write the file** to `CHANGELOG.md` in the repository root.

7. **Report** the result to the user, listing the number of commits categorized and the output file path.

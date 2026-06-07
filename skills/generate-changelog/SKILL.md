# generate-changelog

Generate a structured, categorized `CHANGELOG.md` from this repository's git history.
Uses Claude's own judgment to categorize commits — not keyword matching.

## When to use

Run `/generate-changelog` any time you want to document changes since the last release.
Works on any git repository regardless of commit message style.

## Steps

1. **Find the starting point.** Run:
   ```bash
   git describe --tags --abbrev=0 2>/dev/null
   ```
   If no tags exist, use the first commit: `git rev-list --max-parents=0 HEAD`
   Store this as `$SINCE`.

2. **Get the version label.** The latest tag is the current version. If no tags exist, use `Unreleased`.

3. **Collect commits since `$SINCE`:**
   ```bash
   git log "$SINCE..HEAD" --format="%H|%s|%an|%as" --no-merges
   ```
   If `$SINCE` is the first commit, use `git log --format="%H|%s|%an|%as" --no-merges` instead.

4. **Categorize every commit using your own judgment** into one of:
   - **Added** — new features, capabilities, files, endpoints, commands
   - **Fixed** — bug fixes, crash fixes, incorrect behavior corrections
   - **Changed** — refactors, renames, updates to existing behavior, dependency bumps, CI changes
   - **Removed** — deleted features, deprecated APIs removed, files deleted

   Do not rely solely on conventional-commit prefixes — many real commits don't use them.
   Use the full commit message to infer intent. When genuinely ambiguous, put it in **Changed**.

5. **Clean each commit message** before using it:
   - Strip conventional-commit prefixes: `feat:`, `fix(scope):`, `chore!:`, etc.
   - Capitalize the first letter.
   - Remove trailing periods.
   - Keep the message concise — one line.

6. **Write `CHANGELOG.md`** in this exact format:

```markdown
# Changelog

## [VERSION] – YYYY-MM-DD

### ✨ Added
- Description of change ([`abc1234`](https://github.com/owner/repo/commit/abc1234full))

### 🐛 Fixed
- Description of change ([`def5678`](https://github.com/owner/repo/commit/def5678full))

### 🔧 Changed
- Description of change

### 🗑️ Removed
- Description of change
```

   Rules:
   - Omit any section that has zero entries.
   - Include the 7-character commit SHA after each entry as a link if the repo has a GitHub remote, otherwise plain backtick.
   - Detect the GitHub remote with: `git remote get-url origin 2>/dev/null`
   - Date is today's date in `YYYY-MM-DD` format.

7. **If CHANGELOG.md already exists**, prepend the new section after the `# Changelog` heading —
   do not overwrite previous entries.

8. **Report**: Tell the user how many commits were processed, how they were distributed across categories,
   and the path of the generated file.

## Options (if the user passes arguments after the skill name)

- `--since <ref>` — use this tag/SHA as the starting point instead of the last tag
- `--output <file>` — write to this filename instead of `CHANGELOG.md`
- `--version <label>` — use this string as the version label
- `--preview` — print to screen, do not write to disk

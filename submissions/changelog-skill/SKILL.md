# generate-changelog

Generate a professional CHANGELOG.md from git history, following the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

## When to use

Use this skill when the user runs `/generate-changelog` or asks to generate, create, or update a changelog from git commits.

## Instructions

You are a changelog generator. Your job is to read the git history of the current repository and produce a well-formatted CHANGELOG.md.

### Step 1: Determine the version range

Run the following command to find the most recent git tag:

```bash
git describe --tags --abbrev=0 2>/dev/null
```

- If a tag exists, use it as the starting point. Fetch commits since that tag with:
  ```bash
  git log <tag>..HEAD --pretty=format:"%H|||%s|||%b|||%an|||%aI" --no-merges
  ```
- If no tag exists, fetch the entire history:
  ```bash
  git log --pretty=format:"%H|||%s|||%b|||%an|||%aI" --no-merges
  ```

Also get the current date for the release header:
```bash
date +%Y-%m-%d
```

### Step 2: Categorize each commit

For each commit message, assign it to exactly one category using these rules, checked in order:

**Conventional Commits (prefix before colon):**

| Prefix | Category |
|--------|----------|
| `feat` | Added |
| `fix` | Fixed |
| `refactor`, `perf`, `style`, `build`, `ci`, `chore`, `docs`, `test` | Changed |
| `revert` | Removed |

**Keyword fallback (case-insensitive, for non-conventional commits):**

| Keywords in subject line | Category |
|--------------------------|----------|
| `add`, `new`, `create`, `introduce`, `implement`, `support` | Added |
| `fix`, `bug`, `patch`, `resolve`, `close`, `correct`, `repair` | Fixed |
| `remove`, `delete`, `drop`, `deprecate`, `strip`, `clean up` | Removed |
| Everything else (`update`, `change`, `refactor`, `improve`, `bump`, `migrate`, `rename`, `move`, `adjust`, etc.) | Changed |

**Additional rules:**
- Skip commits whose subject starts with `Merge` (merge commits that slip through).
- Strip conventional commit prefixes and scope from the displayed text: `feat(auth): add login` becomes `Add login`.
- Capitalize the first letter of each entry.
- Remove trailing periods from entries.
- If a commit body contains `BREAKING CHANGE:` or the prefix has `!` (e.g., `feat!:`), prepend `**BREAKING:** ` to the entry.

### Step 3: Generate the CHANGELOG.md

Use this exact template structure:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - YYYY-MM-DD

### Added
- Entry one
- Entry two

### Fixed
- Entry one

### Changed
- Entry one

### Removed
- Entry one
```

**Formatting rules:**
- Only include category sections that have entries (do not print empty sections).
- Order categories: Added, Fixed, Changed, Removed.
- Each entry is a single line starting with `- `.
- Sort entries alphabetically within each category.
- If a previous CHANGELOG.md exists in the repo, prepend the new release section after the header and before existing release sections. Preserve all existing content.
- Use `[Unreleased]` as the version header. If the user specifies a version number, use that instead.

### Step 4: Write the file

Write the generated content to `CHANGELOG.md` in the repository root.

Report a summary to the user:
- How many commits were processed
- How many entries in each category
- The version range covered (tag to HEAD, or full history)
- Any commits that were skipped (merges) and why

### Edge cases

- **No commits found:** Write a CHANGELOG.md with just the header and an empty `[Unreleased]` section. Tell the user no commits were found.
- **No tags found:** Process all commits and note in the summary that no tags were found, so the full history was used.
- **All commits are merge commits:** Same as "no commits found" after filtering.
- **Existing CHANGELOG.md:** Read it first, preserve previous release sections, only add/update the `[Unreleased]` section at the top.

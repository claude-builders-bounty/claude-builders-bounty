# SKILL: Generate CHANGELOG from Git History

## What It Does

Automatically generates a structured `CHANGELOG.md` from a project's git commit history, categorizing changes and formatting them according to Keep a Changelog conventions.

## Invocation

```
/generate-changelog
```

Or run the standalone script:
```
bash changelog.sh
```

## How It Works

### Step 1: Detect Project Root
Finds the `.git` directory to determine the project root.

### Step 2: Get Last Git Tag
```bash
git describe --tags --abbrev=0 2>/dev/null
```
If no tag exists, uses all commits.

### Step 3: Fetch Commits Since Last Tag
```bash
git log <last_tag>..HEAD --pretty=format:"%s"
```

### Step 4: Categorize Each Commit
Scans the commit message for keywords to classify into:

- **Added** — New features
  - Keywords: `add`, `feat`, `new`, `introduce`, `create`, `init`, `implement`
- **Fixed** — Bug fixes
  - Keywords: `fix`, `bug`, `patch`, `repair`, `correct`, `hotfix`, `resolve`
- **Changed** — Changes to existing functionality
  - Keywords: `change`, `update`, `modify`, `refactor`, `improve`, `optimize`, `upgrade`, `deprecate`
- **Removed** — Removed features
  - Keywords: `remove`, `delete`, `drop`, `deprecate`, `uninstall`, `cleanup`
- **Other** — Uncategorized commits

### Step 5: Deduplicate & Sort
Groups identical entries, removes duplicates, sorts each section.

### Step 6: Write CHANGELOG.md
Outputs in Keep a Changelog format:
```markdown
# Changelog

## [Unreleased] - 2026-04-02

### Added
- ...

### Fixed
- ...

### Changed
- ...

### Removed
- ...

### Other
- ...
```

## Sample Output

See `SAMPLE-CHANGELOG.md` for a complete example.

## Dependencies

- `git`
- `bash`
- Standard Unix tools: `grep`, `sort`, `uniq`

## Exit Codes

- `0` — Success
- `1` — Not a git repository
- `2` — No commits found
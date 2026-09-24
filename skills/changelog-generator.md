# Changelog Generator (`changelog.sh`)

Generate a structured `CHANGELOG.md` from your project's git history.

## Setup

1. Copy `changelog.sh` into your repository
2. Make it executable:
   ```bash
   chmod +x changelog.sh
   ```

That's it. No dependencies beyond `git` and `bash`.

## Usage

```bash
# From your repo root
bash changelog.sh
```

The script:
1. Finds the last git tag (e.g., `v1.2.3`)
2. Collects all commits since that tag
3. Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
4. Bumps the patch version (v1.2.3 → v1.2.4)
5. Prepends the new entry to `CHANGELOG.md`

### Categorization Rules

Commits are categorized by conventional commit prefix:

| Category | Prefixes |
|----------|----------|
| **Added** | `feat:`, `feature:`, `add:` |
| **Fixed** | `fix:`, `bug:`, `hotfix:` |
| **Changed** | `refactor:`, `update:`, `perf:`, `style:`, `chore:`, `docs:`, `test:`, `ci:`, `build:` |
| **Removed** | `remove:`, `deprecate:`, `delete:` |

If no conventional commit prefixes are found, it falls back to listing the most recent commits under "Added".

### Example Output

```markdown
# Changelog

## [v1.2.4] - 2026-09-24

### Added
- Implement user authentication via OAuth
- Add dark mode theme support
- New export to PDF functionality

### Fixed
- Fix login redirect loop on expired sessions
- Correct date formatting in reports
- Patch XSS vulnerability in search input

### Changed
- Refactor database connection pooling
- Upgrade to Python 3.12
- Optimize image loading with lazy loading

### Removed
- Deprecate legacy v1 API endpoints
- Remove unused dependencies

## [v1.2.3] - 2026-09-20
...
```

## Sample Output

Tested on [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) repository:

```
## [0.1.0] - 2026-09-24

### Added
- Initialize repository with bounty framework
- Add CLAUDE.md with contribution guidelines
- Create issue templates for bounty submissions
```

## Requirements

- `git` 2.x+
- `bash` 4.x+
- A git repository with at least one commit
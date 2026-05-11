# Sample Output

Command run against the real GitHub repository `octocat/Spoon-Knife` after copying `changelog.sh` and `generate-changelog/` into the repository root:

```bash
bash changelog.sh --dry-run --version 2026-05-10
```

Output:

```markdown
## 2026-05-10

_Generated from git commits all history._

### Added

- Created index page for future collaborative edits (`a30c19e`)
- Create styles.css and updated README (`bb4cc8d`)

### Fixed

- No changes.

### Changed

- Pointing to the guide for forking (`d0dd1f6`)

### Removed

- No changes.
```

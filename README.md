# Changelog Generator

Auto-generates a structured `CHANGELOG.md` from git history.

## Setup (1 step)

```bash
curl -sL https://raw.githubusercontent.com/forevalex/changelog-generator/main/changelog.sh -o changelog.sh
chmod +x changelog.sh
```

## Usage (1 command)

```bash
./changelog.sh [output_file]
```

- If `[output_file]` is omitted, writes to `CHANGELOG.md`
- Fetches commits since the last git tag
- Auto-categorizes into: **Added / Fixed / Changed / Removed / Other**
- Links commits to your GitHub remote

## Example

```bash
cd my-project
./changelog.sh
```

Outputs:
```markdown
## [Unreleased]

### Added
- feat: add user authentication ([`a1b2c3d`](https://github.com/owner/repo/commit/a1b2c3d)) — devname, 2026-06-01

### Fixed
- fix: resolve login redirect loop ([`e4f5g6h`](https://github.com/owner/repo/commit/e4f5g6h)) — devname, 2026-06-02
```

## Categories

| Pattern | Examples |
|---------|----------|
| **Added** | `feat`, `add`, `introduce`, `implement`, `create`, `new` |
| **Fixed** | `fix`, `bug`, `hotfix`, `patch`, `repair`, `correct` |
| **Changed** | `update`, `refactor`, `perf`, `optimize`, `improve`, `enhance`, `change`, `modify`, `chore`, `deps`, `upgrade`, `migrate`, `style`, `docs`, `test`, `ci` |
| **Removed** | `remove`, `delete`, `drop`, `deprecat`, `revert`, `undo`, `clean`, `cleanup` |
| **Other** | Everything else |

## Requirements

- `git`
- `bash` 4.0+

---

Made for [claude-builders-bounty #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

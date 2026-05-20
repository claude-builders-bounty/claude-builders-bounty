# changelog.sh

Generate a structured `CHANGELOG.md` from a project's git history, auto-categorising commits into **Added** / **Fixed** / **Changed** / **Removed**.

## Setup (3 steps)

1. Drop `changelog.sh` into your project root
2. Run `bash changelog.sh`
3. Review `CHANGELOG.md`

## Requirements

- `bash` (≥ 4.0) + `git`

## Usage

```bash
# Generate for current directory
bash changelog.sh

# Generate for a specific repo
bash changelog.sh /path/to/repo
```

Commits since the **last git tag** are included. If no tags exist, the entire history is used.

## Conventional Commit Prefixes

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `create:`, `implement:`, `new:` | Added |
| `fix:`, `patch:`, `correct:`, `hotfix:`, `bug:` | Fixed |
| *(everything else)* | Changed |
| `remove:`, `delete:`, `deprecate:`, `drop:` | Removed |

## Output

Writes a `CHANGELOG.md` like this:

```markdown
# Changelog

_Generated on 2026-05-21 00:35:00 from commits since `v1.0.0`._

## Added
- feat: implement changelog generator (`abc1234`)

## Fixed
- fix: handle empty tag scenario (`def5678`)

## Changed
- chore: bump dependencies (`ghi9012`)

## Removed
- remove: deprecated API endpoint (`jkl3456`)
```

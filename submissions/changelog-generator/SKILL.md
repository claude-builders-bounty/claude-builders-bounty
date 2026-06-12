---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
---

# `/generate-changelog`

Fetches commits since the last git tag and generates a categorized `CHANGELOG.md`.

## Usage

```
/generate-changelog
/generate-changelog path/to/CHANGELOG.md
/generate-changelog ./docs/HISTORY.md
```

Or from the shell:

```bash
bash changelog.sh
bash changelog.sh docs/HISTORY.md
```

## Output sections

| Section     | Conventional commit          | Keywords fallback         |
|-------------|------------------------------|---------------------------|
| **Added**   | `feat:`                      | add, new, initial, introduce |
| **Fixed**   | `fix:`                       | fix, fixed, fixes         |
| **Changed** | `chore:`, `refactor:`, `perf:` | change, refactor, upgrade |
| **Removed** | `revert:`                    | remove, delete, drop      |
| **Security**| —                            | security                  |
| **Deprecated** | —                         | deprecat                  |

## Requirements

- `bash` (any modern version)
- `git`
- A git repository with conventional commits (recommended, optional)

---
name: changelog
description: Generate structured CHANGELOG.md from git history using conventional commit classification. Run when the user asks to generate a changelog or update release notes.
version: 1.0.0
---

# Changelog Generator Skill

## Usage

Invoke via `/generate-changelog` or run `python changelog.py` directly.

### Quick start

```bash
python changelog.py                    # since last tag → HEAD
python changelog.py v1.0.0             # since v1.0.0 → HEAD
python changelog.py v1.0.0 v2.0.0      # between two tags
python changelog.py --stdout            # dry-run, print only
```

### Requirements

- Python 3.8+
- Git repository (run from repo root)

## Classification Rules

| Category     | Conventional Commit Prefixes                     |
|-------------|--------------------------------------------------|
| Added       | `feat`, `add`, `feature`                        |
| Fixed       | `fix`, `bug`, `hotfix`, `patch`                  |
| Changed     | `change`, `update`, `refactor`, `tweak`, `chore` |
| Removed     | `remove`, `drop`, `delete`                       |
| Deprecated  | `deprecate`                                      |
| Security    | `security`, `vuln`, `cve`                        |
| Other       | fallback (everything else)                       |

Merge commits and CI/release bumps are automatically excluded.

## Output Format

Follows [Keep a Changelog](https://keepachangelog.com) conventions with date-stamped entries, grouped by category.

## Example

See `SAMPLE_OUTPUT.md` for real output from the `charmbracelet/gum` repo.
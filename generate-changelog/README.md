# generate-changelog

Turns git history since the last tag into a Keep-a-Changelog style `CHANGELOG.md`.

Works as `bash changelog.sh` or `python3 changelog.py`. If you use Claude Code, invoke it as `/generate-changelog` after copying the files into the repo (or add a skill that shells out to `changelog.sh`).

## Setup (3 steps)

1. Copy `changelog.sh` and `changelog.py` into the repository (any folder).
2. From the repo root: `python3 path/to/changelog.py`  
   or: `bash path/to/changelog.sh`
3. Commit the generated `CHANGELOG.md`.

Requires `git` on PATH. Python 3.10+. Conventional-commit prefixes (`feat:`, `fix:`, …) are categorized first; otherwise the subject is keyword-scanned.

## Sample

`sample-CHANGELOG.md` was generated from a real repo (`md-notebook-demo` on 2026-08-18) with this command:

```bash
python3 changelog.py --stdout
```

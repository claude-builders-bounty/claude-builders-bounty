# Submission Notes

Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1

## Summary

This package adds a changelog generator that creates a structured `CHANGELOG.md` from git history. It supports:

- `python generate_changelog.py`
- `bash changelog.sh`
- `python generate_changelog.py --since <tag-or-ref> --output CHANGELOG.md`
- A Claude Code-style `SKILL.md` for `/generate-changelog`

## Verification

```powershell
python -m py_compile .\generate_changelog.py .\test_generate_changelog.py
python .\test_generate_changelog.py
python .\generate_changelog.py --output .\CHANGELOG.md
```

All commands passed locally.

## Files

- `generate_changelog.py`
- `changelog.sh`
- `SKILL.md`
- `CHANGELOG.md`
- `test_generate_changelog.py`
- `README.md`

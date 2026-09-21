# Verification — generate-changelog (bounty #1)

Local reproduction (stdlib only; no network required after clone):

```bash
python3 -m py_compile skills/generate-changelog/scripts/changelog.py
bash -n changelog.sh
python3 skills/generate-changelog/scripts/changelog.py --help
# optional: run against any git repo with tags
# python3 skills/generate-changelog/scripts/changelog.py --cwd /path/to/repo --stdout
```

## Acceptance checklist

| Criterion | Evidence |
|-----------|----------|
| `/generate-changelog` or `bash changelog.sh` | `SKILL.md` + root `changelog.sh` wrapper |
| Commits since last tag | `git describe --tags --abbrev=0` then `git log TAG..HEAD` |
| Added / Fixed / Changed / Removed | Conventional + keyword rules in `changelog.py` |
| Formatted CHANGELOG.md | Keep-a-Changelog sections |
| Real GitHub sample | `SAMPLE_OUTPUT.md` + `examples/sample-CHANGELOG.md` from expressjs/express since `v5.2.1` |
| README ≤ 3 setup steps | `skills/generate-changelog/README.md` |

## Notes for maintainers

- Fork CI may need a one-click approval for first-time contributors.
- No pip deps; Python 3 stdlib only.

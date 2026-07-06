# Acceptance checklist — Bounty #1 ($50)

- [x] Claude Code skill format (`SKILL.md` + `/generate-changelog` trigger)
- [x] `changelog.sh` — standalone bash generator (1-command setup)
- [x] `changelog.py` — Python fallback with git tag detection
- [x] Categorizes commits: Added / Fixed / Changed / Removed
- [x] Generates structured `CHANGELOG.md` since last tag
- [x] Sample output: `samples/CHANGELOG.sample.md`
- [x] Tests: `python test_changelog.py` (categorize, full gen, since-last-tag)

/opire try — PR ready for merge.

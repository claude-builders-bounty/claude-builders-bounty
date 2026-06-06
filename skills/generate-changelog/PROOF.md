# Bounty #1 verification map

Maps each acceptance criterion to the exact command or artifact in this PR.

| Criterion | Evidence |
|-----------|----------|
| `/generate-changelog` or `bash changelog.sh` | `SKILL.md` (`name: generate-changelog`) + `changelog.sh` |
| Fetches commits since last git tag | Default range `${SINCE_TAG}..HEAD` in `changelog.sh` |
| Auto-categorizes Added / Fixed / Changed / Removed | `commit_type()` + section builders in `changelog.sh` |
| Outputs formatted `CHANGELOG.md` | Keep a Changelog-style headers and bullet lists |
| Tested on a real repo (sample in PR) | `samples/CHANGELOG.sample.md` generated from this repo |
| README with setup in ≤3 steps | `README.md` Quick start (3 steps) |

## Commands

```bash
# Regression tests (22 cases)
bash skills/generate-changelog/tests/test_changelog.sh

# Generate changelog for current repo
bash skills/generate-changelog/changelog.sh

# Preview without writing a file
bash skills/generate-changelog/changelog.sh --preview
```

Expected test output ends with `Tests: 22 passed, 0 failed`.

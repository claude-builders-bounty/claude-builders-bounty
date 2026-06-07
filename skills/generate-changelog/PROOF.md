# Bounty #1 verification map

Maps each acceptance criterion to the exact command or artifact in this PR.

| Criterion | Evidence |
|-----------|----------|
| `/generate-changelog` or `bash changelog.sh` | `SKILL.md` (`name: generate-changelog`) + repo-root `changelog.sh` |
| Fetches commits since last git tag | Default range `${SINCE_TAG}..HEAD` in `changelog.sh` |
| Auto-categorizes Added / Fixed / Changed / Removed | `commit_type()` + section builders in `changelog.sh` |
| Breaking changes surfaced | `feat!:` / `BREAKING CHANGE` subjects get a **Breaking** section |
| Append to existing changelog | `--append` prepends a release while preserving prior entries |
| Outputs formatted `CHANGELOG.md` | Keep a Changelog-style headers and bullet lists |
| Tested on a real repo (sample in PR) | `samples/CHANGELOG.sample.md` generated from this repo |
| README with setup in ≤3 steps | `README.md` Quick start (3 steps) |

## Commands

```bash
# Regression tests (37 cases)
bash skills/generate-changelog/tests/test_changelog.sh

# Generate changelog for current repo (repo-root entrypoint)
bash changelog.sh

# Preview without writing a file
bash changelog.sh --preview

# Prepend a release to an existing changelog
bash changelog.sh --since v1.0.0 --version 1.1.0 --append
```

Expected test output ends with `Tests: 37 passed, 0 failed`.

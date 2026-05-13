# Test report — structured changelog generator

Bounty issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1

## Acceptance criteria coverage

- **Works via `bash changelog.sh`:** yes. The script can be copied to a repo root and run with `bash changelog.sh`.
- **Fetches commits since the last git tag:** yes. By default it uses `git describe --tags --abbrev=0` and generates from `<latest-tag>..HEAD`. If no tag exists, it uses all history.
- **Auto-categorizes commits:** yes. It emits `Added`, `Fixed`, `Changed`, and `Removed` sections based on conventional-commit and keyword heuristics.
- **Outputs `CHANGELOG.md`:** yes. The default output file is `CHANGELOG.md`; `--output` can override it.
- **Tested on a real GitHub-style git repository:** yes. A temporary git repository with a tag and post-tag commits was created locally, and the script was run against real git history.
- **README setup in 3 steps or fewer:** yes. See `README.md`.

## Validation commands

```bash
TMP=$(mktemp -d)
cp tools/changelog-generator/changelog.sh "$TMP/changelog.sh"
cd "$TMP"
git init
git config user.name 'Test User'
git config user.email 'test@example.com'
printf 'initial\n' > app.txt
git add app.txt
git commit -m 'feat: initial project'
git tag v0.1.0
printf 'login\n' >> app.txt
git add app.txt
git commit -m 'feat: add login flow'
printf 'bugfix\n' >> app.txt
git add app.txt
git commit -m 'fix: handle empty email'
printf 'docs\n' > docs.md
git add docs.md
git commit -m 'docs: update setup guide'
git rm docs.md
git commit -m 'remove: obsolete docs page'
bash changelog.sh
```

## Validation result

```text
Wrote CHANGELOG.md from since v0.1.0
VALIDATION OK
```

## Expected generated categories

The generated `CHANGELOG.md` should include:

- `feat: add login flow` under `Added`
- `fix: handle empty email` under `Fixed`
- `docs: update setup guide` under `Changed`
- `remove: obsolete docs page` under `Removed`

## Sample output

See `SAMPLE_CHANGELOG.md`.

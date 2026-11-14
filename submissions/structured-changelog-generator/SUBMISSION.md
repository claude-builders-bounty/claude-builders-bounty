# Submission: CHANGELOG generator (bounty #1, $50)

**Bounty:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
**Reward:** $50 via Opire (Stripe) on merge.
**Status:** **已提交** — claim 评论：https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1#issuecomment-6885144314
**PR:** https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5223
**等待：** 维护者审核/合并；合并并付款前不计收入。

## Files

| File | Purpose |
|---|---|
| `changelog.py` | Generate a structured `CHANGELOG.md` from local git history or GitHub API. |
| `changelog.sh` | Bash wrapper (`bash changelog.sh ...`). |
| `SKILL.md` | Claude Code skill instructions for `/generate-changelog`. |
| `README.md` | 3-step setup, usage, categories. |
| `tests/test_changelog.py` | 3 unit tests. |
| `sample-output-requests.md` | Real output generated from `psf/requests` via GitHub API. |

## Acceptance mapping

- [x] Works via `/generate-changelog` command (`SKILL.md`) or `bash changelog.sh`.
- [x] Fetches commits since the last tag (`git describe --tags --abbrev=0`, or GitHub tags API).
- [x] Auto-categorizes into Added / Fixed / Changed / Removed / Other.
- [x] Outputs a formatted `CHANGELOG.md`.
- [x] Tested on a real GitHub repo: `psf/requests`, 30 commits since latest tag, output in `sample-output-requests.md`.
- [x] README setup in 3 steps.

## Test evidence

```text
$ python3 -m unittest discover -s tests -v
Ran 3 tests in 2.713s
OK
```

Real GitHub API run:

```text
$ python3 changelog.py --github psf/requests --output sample-output-requests.md
wrote sample-output-requests.md (30 commits)
```

Sample output starts with:

```markdown
# Changelog

_Generated at ..._

## Added
- Add AI Policy ([c4367f2](...))
...
```

## How to submit (needs GitHub account)

1. Comment `/opire try` on issue #1.
2. Fork the bounty repo, add these files under a submission directory, open a PR titled `[Bounty #1] Structured CHANGELOG generator (CLI + skill)`.
3. Payment releases automatically on merge.

## Notes / limitations

- GitHub API mode is for environments where `git clone` is unavailable; local mode is faster.
- Unauthenticated GitHub API is rate-limited; set `GITHUB_TOKEN` for heavier use.
- Categorization is heuristic (conventional commit prefixes + verb keywords).

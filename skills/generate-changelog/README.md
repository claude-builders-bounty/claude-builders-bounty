# Generate a changelog from git history

Generates a categorized `CHANGELOG.md` from the commits since the last git tag.
Pure bash — only git is required. Works as a script or as a Claude Code skill.

Categorizes into **Added / Fixed / Changed / Removed** using Conventional Commit
prefixes when present (`feat:`, `fix:`, `revert:`, `refactor:`, …) and plain-language
keyword matching otherwise (add / fix / remove / …). Merge commits and duplicate
subjects are skipped; entries carry a short commit hash.

## Setup

1. `git clone` this repo (or copy `skills/generate-changelog/` into your project).
2. `bash skills/generate-changelog/changelog.sh` — writes `CHANGELOG.md` from the
   commits since the last tag (`--from v1.2.0` to pick another start, `--out` to
   choose the output file).
3. Optionally `bash skills/generate-changelog/tests/test_changelog.sh` to verify the
   categorization rules in a throwaway repository.

To use it as a Claude Code skill, copy the `generate-changelog/` directory into
`.claude/skills/` and invoke `/generate-changelog`.

## Example

```bash
$ bash changelog.sh --from v2.3.0
Wrote 39 commits in v2.3.0..HEAD to CHANGELOG.md
```

```
## [Unreleased (since v2.3.0)]

### Added

- Add named beta types for unified metrics and RBAC delete responses (`62b05ab`)
```

`examples/SAMPLE_CHANGELOG.md` is the full real output from running the script on
[anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python)
(commits since `v2.3.0`).

## Files

| File | Purpose |
| --- | --- |
| `changelog.sh` | the generator (`--repo`, `--from`, `--out`) |
| `SKILL.md` | Claude Code skill instructions for `/generate-changelog` |
| `tests/test_changelog.sh` | self-contained tests (28 checks) |
| `examples/SAMPLE_CHANGELOG.md` | real sample output |

# Test Provenance

## Test 1 — since-tag path (the sample output in this directory)

- **Repository**: NousResearch/hermes-agent (public GitHub repo)
- **Method**: shallow clone (`git clone --depth 50`), then
  `bash changelog.sh <clone>` — no repository files were modified beyond
  writing `CHANGELOG.md` into the clone
- **Range**: since tag `rc.11-v0.21.7` (last tag at clone time)
- **Result**: 56 commits categorized — 13 Added, 28 Fixed, 15 Changed, 0 Removed
- **Output**: `sample-changelog.md` is the verbatim generated file

## Test 2 — no-tags path

- **Repository**: npgum/sophia-tmlanguage (public GitHub repo)
- **Method**: clone + `bash changelog.sh <clone>`
- **Result**: full-history range (no tags), 1 commit categorized under Changed

## Test 3 — idempotency

- Ran the script twice against the same clone; verified exactly one
  `## Unreleased` section exists after the second run (`grep -c '^## Unreleased'`
  returns 1) and the released sections are unchanged.

## Edge cases covered

- Repo with no tags (falls back to full history)
- Re-run replaces the Unreleased section instead of duplicating it
- Merge commits and version-bump commits are filtered
- Non-conventional commit messages fall back to keyword classification

## Summary
Adds a portable `changelog.sh` plus a Claude Code skill that regenerates `CHANGELOG.md` from commits since the last git tag, with Added/Fixed/Changed/Removed sections and a sample run on this repository.

## Risks
- Conventional-commit heuristics can mis-bucket vague subjects into Changed.
- Running against a huge history with no tags may produce a noisy first changelog.

## Suggestions
- Add a `--since <ref>` flag for release managers who do not use tags.
- Include a short unit test corpus of subject lines → categories.

## Confidence
High — the diff is a self-contained script/skill with clear acceptance criteria and a checked-in sample.

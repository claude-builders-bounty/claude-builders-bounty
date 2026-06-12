# PR Draft: Add Generate Changelog Skill

Closes #1.

## Summary

- Adds a Claude Code skill with `SKILL.md` for generating `CHANGELOG.md` from git history.
- Adds `bash skills/generate-changelog/scripts/changelog.sh`.
- Fetches commits since the latest git tag, or full history when no tag exists.
- Auto-categorizes commits into Added, Fixed, Changed, and Removed.
- Includes sample output generated from this real repository.

## Acceptance Criteria

- Works via `bash skills/generate-changelog/scripts/changelog.sh`
- Fetches commits since the last git tag
- Auto-categorizes into `Added` / `Fixed` / `Changed` / `Removed`
- Outputs `CHANGELOG.md`
- Includes sample output from a real GitHub repo
- README setup has 3 steps

## Verification

```bash
bash skills/generate-changelog/scripts/changelog.sh /tmp/claude-builders-bounty-changelog.md
python3 skills/generate-changelog/validate_changelog_skill.py
```

Observed:

```text
generate changelog skill validation passed
```

## Local Submit Steps

```bash
git checkout bounty-1-generate-changelog
git add README.md skills/generate-changelog/SKILL.md skills/generate-changelog/README.md skills/generate-changelog/scripts/changelog.sh skills/generate-changelog/samples/claude-builders-bounty.md skills/generate-changelog/validate_changelog_skill.py
git commit -m "Add generate changelog skill"
git push <your-fork> bounty-1-generate-changelog
```

## Claim

After opening the PR, comment on issue #1:

```text
/opire try

Submitted PR: <PR URL>

This adds a Claude Code skill and bash script that generate a structured CHANGELOG.md from git history since the latest tag, with categorized sections, sample output, and validation.
```

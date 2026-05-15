# generate-changelog

Generates a structured `CHANGELOG.md` from your project's git history.

## Trigger

```
/generate-changelog
```

## What It Does

1. Finds commits since the last git tag (or all commits if no tags exist)
2. Auto-categorizes each commit into `Added`, `Fixed`, `Changed`, or `Removed`
3. Writes a Keep-a-Changelog-formatted `CHANGELOG.md` to your project root
4. Prints a summary of what was written

## Instructions

When the user runs `/generate-changelog`:

1. Run `bash ~/.claude/skills/changelog.sh` and capture its output.
2. Show the user the generated CHANGELOG content.
3. Confirm that `CHANGELOG.md` has been written to the project root.
4. Offer to commit it: `git add CHANGELOG.md && git commit -m "docs: update CHANGELOG"`.

If there are no commits or no git repository, explain clearly and stop.

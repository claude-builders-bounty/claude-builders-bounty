# Generate Changelog

Generate a structured `CHANGELOG.md` from git history.

## Setup

```bash
chmod +x skills/generate-changelog/changelog.sh
bash skills/generate-changelog/changelog.sh
```

The first command makes the generator executable. The second command writes `CHANGELOG.md` in the current repository.

## What It Does

- Detects the latest git tag and reads commits from that tag to `HEAD`.
- Falls back to all commits when the repository has no tags.
- Groups non-merge commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes clean Markdown that can be edited before release.

## Optional Output Path

```bash
bash skills/generate-changelog/changelog.sh RELEASE_NOTES.md
```

## Verification

This was tested against this repository. Because the repository currently has no tags, the script used all commits and generated the sample in `sample-output.md`.

---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a repository's git history since the latest tag.
---

# Generate Changelog

Use this skill when the user asks for `/generate-changelog`, a release changelog, or a structured summary of git history.

## Workflow

1. Confirm you are inside the target git repository.
2. Run `bash changelog.sh` from the repository root.
3. Review `CHANGELOG.md` and adjust wording only when the generated commit subjects need clearer release language.

## Behavior

The script fetches tags from `origin`, finds the latest reachable tag with `git describe --tags --abbrev=0`, and collects non-merge commits from that tag to `HEAD`. If the repository has no tags, it uses the full git history.

Commits are grouped into:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

The generated changelog includes commit links for GitHub remotes, commit dates, and authors.

## Command

```bash
bash changelog.sh
```

To write somewhere else:

```bash
bash changelog.sh --output RELEASE_NOTES.md
```

---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a repository's git history.
---

# Generate Changelog

Use this skill when a user wants a changelog, release notes, or a categorized summary of commits.

## Workflow

1. Confirm you are in the target git repository.
2. Run `bash changelog.sh` from the repository root.
3. Review `CHANGELOG.md` for wording, duplicates, and release-specific context before presenting it.

## Options

```bash
bash changelog.sh --output CHANGELOG.md
bash changelog.sh --since v1.2.0
```

## Output Rules

- Keep the generated sections: `Added`, `Fixed`, `Changed`, `Removed`.
- If commit messages are unclear, improve the final text by editing the changelog after generation.
- Do not invent release details that are not supported by the git history.
- For public release notes, mention the tag or range used to generate the file.

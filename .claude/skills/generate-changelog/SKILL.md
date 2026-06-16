---
name: generate-changelog
description: Generate a structured CHANGELOG.md from the current repository's git history since the latest tag.
---

# Generate Changelog

Use this skill when the user asks for `/generate-changelog`, "generate a changelog", or "summarize commits since the last tag".

Run the repository script from the project root:

```bash
bash changelog.sh
```

If the user wants a custom output path, pass it as the first argument:

```bash
bash changelog.sh RELEASE-NOTES.md
```

The generated file must include:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

The script reads the latest reachable git tag with `git describe --tags --abbrev=0`, then analyzes commits in `<tag>..HEAD`. If no tag exists, it documents that fallback and uses all commits.

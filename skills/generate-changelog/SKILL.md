# Generate Changelog

Use this skill when the user asks for `/generate-changelog`, wants a
`CHANGELOG.md`, or asks to summarize git history since the latest tag.

## Command

Run the bundled script from the repository root:

```bash
bash skills/generate-changelog/changelog.sh
```

Optional output path:

```bash
bash skills/generate-changelog/changelog.sh --output docs/CHANGELOG.md
```

## Workflow

1. Verify the current directory is inside a git repository.
2. Find the latest reachable git tag with `git describe --tags --abbrev=0`.
3. Collect commits from that tag to `HEAD`; if no tag exists, collect all
   commits.
4. Categorize commits into `Added`, `Fixed`, `Changed`, and `Removed`.
5. Write a Keep a Changelog-style `CHANGELOG.md`.
6. Report the tag range, output path, and category counts.

## Rules

- Do not invent changes. Only use commit subjects from git history.
- Do not include merge commits because they duplicate the underlying work.
- Keep commit hashes in the output so maintainers can audit each entry.
- If there are no commits since the last tag, still write a valid changelog with
  an explicit "No changes" entry.

# Generate Changelog

Use this skill when the user asks for `/generate-changelog`, asks to create a
`CHANGELOG.md`, or wants release notes generated from git history.

## Command

Run the changelog generator from the repository root:

```bash
bash changelog.sh
```

To write to a custom path:

```bash
bash changelog.sh docs/CHANGELOG.md
```

## What It Does

- Detects the latest git tag and reads commits from that tag through `HEAD`.
- Falls back to all commits when the repository has no tags.
- Categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown `CHANGELOG.md` with an `Unreleased` section.

## Verification

After running the script, inspect the generated file and confirm the sections
match the recent commit history:

```bash
git log --oneline --decorate --max-count=20
sed -n '1,120p' CHANGELOG.md
```

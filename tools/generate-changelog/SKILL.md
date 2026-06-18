# Generate Changelog Skill

Use this skill when asked to generate, refresh, or preview a structured
`CHANGELOG.md` from git history.

## Command

Run from the repository root:

```bash
bash tools/generate-changelog/changelog.sh
```

To write to a preview file instead of `CHANGELOG.md`:

```bash
bash tools/generate-changelog/changelog.sh /tmp/CHANGELOG.preview.md
```

## Behavior

- Uses commits since the latest git tag when a tag exists.
- Falls back to the full non-merge git history when no tag exists.
- Groups commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Supports conventional commit scopes such as `feat(api):` and `fix(ui):`.
- Writes a Markdown changelog suitable for review before committing.

## Verification

```bash
bash tools/generate-changelog/test-changelog.sh
```

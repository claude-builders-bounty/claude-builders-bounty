# Generate Changelog

`changelog.sh` creates a structured `CHANGELOG.md` from the current repository's
git history. It reads commits since the latest git tag when one exists; otherwise
it uses the full non-merge history.

## Setup

1. Copy `tools/generate-changelog/changelog.sh` into a git repository.
2. Run `bash tools/generate-changelog/changelog.sh`.
3. Review the generated `CHANGELOG.md` before committing it.

## Categories

The script groups commit subjects into:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

It recognizes common prefixes such as `feat:`, `feat(api):`, `fix:`,
`remove:`, `delete:`, and keyword-based commit subjects.

## Output Path

Pass a custom output file as the first argument:

```bash
bash tools/generate-changelog/changelog.sh /tmp/CHANGELOG.preview.md
```

## Verification

```bash
bash tools/generate-changelog/test-changelog.sh
```

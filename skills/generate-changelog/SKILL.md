# Generate Changelog

Use this skill when a user asks for a structured `CHANGELOG.md` generated from a repository's git history.

## Workflow

1. Run `bash changelog.sh` from the repository root.
2. Review the generated `CHANGELOG.md` and keep the four sections: `Added`, `Fixed`, `Changed`, and `Removed`.
3. If the user wants a preview only, run `bash changelog.sh --stdout`.

## Rules

- Generate from commits since the latest git tag.
- If the repository has no tags, generate from the full history and say that no tag was found.
- Categorize commits by Conventional Commit type first, then by action words in the subject.
- Keep commit short SHAs in the output so users can trace each entry back to source history.
- Do not invent changes that are not present in git history.

## Command

```bash
bash changelog.sh
```

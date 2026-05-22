# Generate Changelog

Generate a structured `CHANGELOG.md` from the current repository's git history.

Run:

```bash
bash changelog.sh
```

Use these options when needed:

```bash
bash changelog.sh --stdout
bash changelog.sh --from v1.2.0 --to HEAD
bash changelog.sh --repo ../my-project --output ../my-project/CHANGELOG.md
```

After running, inspect the generated `CHANGELOG.md` and verify the commit categories:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

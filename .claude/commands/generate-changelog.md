Generate a structured `CHANGELOG.md` from this repository's git history.

Steps:

1. Run `bash changelog.sh`.
2. Read the generated `CHANGELOG.md`.
3. Summarize which git tag was used and which sections were populated.

If the user supplies arguments, pass them through to the script. Examples:

```bash
bash changelog.sh --since v1.2.0 --version 1.3.0
bash changelog.sh --dry-run
```

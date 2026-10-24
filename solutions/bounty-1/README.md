# Changelog generator

Run from any Git repository:

```bash
python3 solutions/bounty-1/changelog.py --version 1.2.0
```

The script reads commit subjects from the latest reachable Git tag through `HEAD`; when no tag exists, it uses all reachable non-merge commits. Conventional prefixes are mapped to `Added`, `Fixed`, `Changed`, and `Removed`. Unknown prefixes are kept under `Changed` rather than discarded.

Useful options:

- `--output path/to/CHANGELOG.md` changes the output path.
- `--append` prepends the new section to an existing changelog.
- `--version 1.2.0` changes the Markdown heading.

Requires Python 3.10+ and Git. The script does not rewrite commit history or call external services.

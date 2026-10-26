# Generate Changelog Skill

Generate a structured changelog from commits made after the latest reachable Git tag.

## Usage

```bash
bash changelog.sh
```

Optional:

```bash
bash changelog.sh --repository /path/to/project --output CHANGELOG.md
```

The command uses the latest reachable tag as the boundary. If no tag exists, it creates an `Unreleased` section containing the repository history. Merge commits are omitted.

## Classification

Conventional Commit prefixes map to:

- `feat` → `Added`
- `fix` → `Fixed`
- `refactor`, `perf`, `docs`, `test`, `build`, `ci`, `chore`, `style`, `revert` → `Changed`
- explicit `remove`, `delete`, and `deprecate` types → `Removed`

For non-conventional subjects, leading verbs such as `add`, `fix`, `update`, and `remove` are recognized. Any other subject is placed in `Changed` so the output remains complete without inventing a fifth category.

## Tests

```bash
python3 tests/test_generate_changelog.py
```

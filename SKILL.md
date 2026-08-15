---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history (conventional-commit grouped). Use when the user asks to create or update a changelog, or runs /generate-changelog.
---

# Generate Changelog

Produce a structured `CHANGELOG.md` from the repo's git history, grouped by
change type (Added / Fixed / Changed / Docs / Tests / Chore / Other).

## How

Run the bundled helper:

```bash
bash changelog.sh            # since last version tag, else full history
bash changelog.sh v1.2.0     # explicit base ref
```

The script groups commits by conventional-commit prefix (`feat:` -> Added,
`fix:` -> Fixed, `docs:` -> Docs, `refactor:`/`perf:` -> Changed, `test:` ->
Tests, `chore:` -> Chore, anything else -> Other) and prints a Markdown
changelog to stdout. Redirect to a file to persist it:

```bash
bash changelog.sh > CHANGELOG.md
```

## Steps
1. Determine the base ref (last tag via `git describe --tags --abbrev=0`, or use
   the user-supplied arg).
2. Run `changelog.sh` with that base.
3. Show the result; if the user wants it saved, write `CHANGELOG.md` at repo root
   (respect an existing `CHANGELOG.md` — prepend a new section rather than
   overwriting past entries).
4. Report the path and a one-line summary of counts per group.

## Notes
- Skip merge commits and blank messages.
- Keep commit hashes short (`%h`).
- Never rewrite the user's actual git history — this only reads it.

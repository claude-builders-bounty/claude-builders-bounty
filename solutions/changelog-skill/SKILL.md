---
name: generate-changelog
description: Use when asked to write, update, or regenerate a CHANGELOG from git history. Generates a structured CHANGELOG.md (Added/Fixed/Changed/Removed) from commits since the last git tag.
---

# generate-changelog

Run the bundled script from the repo root:

```bash
bash changelog.sh            # unreleased-since-last-tag, writes CHANGELOG.md
bash changelog.sh --all      # regenerate every tag section
bash changelog.sh --stdout   # preview without writing
```

Rules:
- Always run `--stdout` first and show the user the diff before overwriting an existing CHANGELOG.md.
- If the repo has no tags yet, the script still works: everything lands in "Unreleased".
- Categorization is conventional-commits aware (`feat:`/`fix:`/`remove:`→ categories);
  non-conventional commits are bucketed by keyword heuristics and default to "Changed" —
  review-before-commit is the human step, never auto-commit the result.

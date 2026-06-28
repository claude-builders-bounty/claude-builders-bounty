Command:

```bash
python -m claude_review.cli --pr https://github.com/cli/cli/pull/11703
```

Output:

```markdown
## Summary of changes

This PR changes 1 file(s), with 46 added line(s) and 56 removed line(s). The detected change areas are: runtime code.
The largest files in the diff are `api/queries_projects_v2.go`.

## Identified risks

- Runtime code changed without obvious test file updates in this diff.

## Improvement suggestions

- Add or link targeted tests that exercise the changed runtime behavior.
- Include manual verification notes or screenshots when behavior is user-facing.

## Confidence score: Medium

This review is based on diff metadata and lightweight heuristics; it should complement, not replace, a human review.
```

Command:

```bash
python -m claude_review.cli --pr https://github.com/python/cpython/pull/135000
```

Output:

```markdown
## Summary of changes

This PR changes 3 file(s), with 6 added line(s) and 0 removed line(s). The detected change areas are: documentation, runtime code.
The largest files in the diff are `Lib/_pyrepl/utils.py`, `Misc/NEWS.d/next/Library/2025-06-01-11-14-00.gh-issue-134953.ashdfs.rst`, `Lib/_colorize.py`.

## Identified risks

- Runtime code changed without obvious test file updates in this diff.

## Improvement suggestions

- Add or link targeted tests that exercise the changed runtime behavior.
- Check links, headings, and examples so readers can follow the updated guidance.
- Include manual verification notes or screenshots when behavior is user-facing.

## Confidence score: Medium

This review is based on diff metadata and lightweight heuristics; it should complement, not replace, a human review.
```

## Summary of Changes

This PR changes 2 files with 86 additions and 0 deletions.
The touched areas are primarily `hooks`, so review should focus on behavior in those paths.
I do not see test files in the diff, so runtime coverage should be checked before merge.

## Identified Risks

- No test files were detected in the diff, so behavioral changes may be under-covered.

## Improvement Suggestions

- Run the project-specific test command and include the result before merge.
- Add or update focused tests for the changed behavior, especially edge cases.
- Check that documentation examples still match the implemented behavior.

## Confidence Score

Medium

<details>
<summary>Changed files analyzed</summary>

- `hooks/pre-tool-use/README.md` (+25/-0, 1 hunks)
- `hooks/pre-tool-use/pre-tool-use.py` (+61/-0, 1 hunks)

</details>

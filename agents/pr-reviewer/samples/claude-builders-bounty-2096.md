## Summary of Changes

This PR changes 8 files with 1043 additions and 0 deletions.
The touched areas are primarily `agents, hooks, scripts`, so review should focus on behavior in those paths.
I do not see test files in the diff, so runtime coverage should be checked before merge.

## Identified Risks

- Large diff size increases the chance of missed regressions during review.
- No test files were detected in the diff, so behavioral changes may be under-covered.
- Configuration changes can behave differently across environments.
- Security-sensitive terms such as auth, tokens, SQL, subprocess, or permissions appear in changed lines.

## Improvement Suggestions

- Run the project-specific test command and include the result before merge.
- Add or update focused tests for the changed behavior, especially edge cases.
- Manually inspect changed auth, token, SQL, subprocess, or permission paths for abuse cases.
- Check that documentation examples still match the implemented behavior.

## Confidence Score

Medium

<details>
<summary>Changed files analyzed</summary>

- `agents/pr-review/README.md` (+83/-0, 1 hunks)
- `agents/pr-review/action.yml` (+62/-0, 1 hunks)
- `agents/pr-review/examples/fastapi-13456.md` (+22/-0, 1 hunks)
- `agents/pr-review/review.py` (+332/-0, 1 hunks)
- `hooks/pre-tool-use/README.md` (+73/-0, 1 hunks)
- `hooks/pre-tool-use/pre-tool-use.py` (+137/-0, 1 hunks)
- `scripts/changelog-readme.md` (+68/-0, 1 hunks)
- `scripts/changelog.sh` (+266/-0, 1 hunks)

</details>

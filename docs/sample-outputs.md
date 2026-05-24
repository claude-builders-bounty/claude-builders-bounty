# claude-review Sample Outputs

These examples were generated from public GitHub pull requests with `claude-review`.
They are illustrative snapshots, not reviews posted back to GitHub.

## Example 1: pallets/flask#5827

Command:

```bash
claude-review --pr https://github.com/pallets/flask/pull/5827
```

Output:

```markdown
# Claude Review

## Summary of Changes
- PR: [pallets/flask#5827](https://github.com/pallets/flask/pull/5827) - clarify 415 vs 400 errors for request.json
- Author: `adityasah104`; state: `merged`; base/head: `stable <- docs-clarify-json-415-error`
- Scope: 1 file(s), +5/-3 lines, fetched via `gh`.
- Changed areas: .rst x1; docs/patterns/javascript.rst.

## Risks
- No major heuristic risks detected from the diff.

## Improvement Suggestions
- Keep the PR description current with validation steps and any reviewer context.
- Run the repository's normal test and lint suite before merge.

## Confidence
High
```

## Example 2: pallets/werkzeug#3064

Command:

```bash
claude-review --pr https://github.com/pallets/werkzeug/pull/3064
```

Output:

```markdown
# Claude Review

## Summary of Changes
- PR: [pallets/werkzeug#3064](https://github.com/pallets/werkzeug/pull/3064) - GitHub Actions: Add Python 3.14 and 3.14t to the testing
- Author: `cclauss`; state: `merged`; base/head: `stable <- patch-1`
- Scope: 4 file(s), +40/-11 lines, fetched via `gh`.
- Changed areas: .yaml x1, .toml x1, .py x1, .lock x1; .github/workflows/tests.yaml, pyproject.toml, tests/test_serving.py, uv.lock.

## Risks
- CI/workflow changes can affect release gates or repository permissions.
- Dependency or lockfile changes can alter runtime behavior beyond the visible source diff.

## Improvement Suggestions
- Document why dependency changes are needed and verify lockfile consistency.
- Confirm workflow permissions and required checks still match the repository policy.
- Identify generated artifacts and the command used to regenerate them.

## Confidence
Medium
```

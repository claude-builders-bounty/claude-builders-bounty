## Summary
This PR, **Add security warning when dev server binds to non-localhost**, changes 1 file(s): src/flask/app.py. The fetched diff contains approximately +17/-0 changed lines. PR notes mention: ## Summary  Adds a `RuntimeWarning` when Flask's development server is bound to a non-localhost address. The Werkzeug debugger allows arbitrary code execution when exposed to the network, yet many tutorials and quick-start guides instruct users to bind to `0.0.0.0` without warning them of the risks.

## Identified risks
- No obvious high-risk pattern is visible from the diff alone; remaining risk is hidden behavior not covered by tests.

## Improvement suggestions
- Add or update tests that cover the changed behavior before merge.
- Document any user-facing behavior or setup changes in the PR description or README.
- Confirm backwards compatibility for callers/configuration touched by this change.

## Confidence
High — based on diff size, touched files, and visible risk patterns from https://github.com/pallets/flask/pull/6018.

# PR Review: automatic options as separate route

> https://github.com/pallets/flask/pull/5918

## Summary
This PR refactors Flask's automatic `OPTIONS` response handling from an ad-hoc check inside `dispatch_request` into a proper named route (`_automatic_options`) registered at startup. It simultaneously fixes a long-standing weakref cycle on the static file view (issue #3761) by replacing the lambda+weakref with a module-level `_static_view` function. The result is cleaner dispatch logic and one fewer special-case branch in the hot request path.

## Identified Risks
- **Werkzeug version assumption**: The PR description notes it relies on `except Exception` (rather than `except DuplicateRuleError`) until Werkzeug 3.2 ships. Catching broad `Exception` during route registration could silently swallow unrelated errors if the `add_url_rule` call fails for a different reason.
- **`flask routes` filter by string**: The `cli.py` filter `if rule.endpoint == "_automatic_options"` is a magic string. If the internal endpoint name ever changes, the CLI will start showing noise without any test catching it.
- **`provide_automatic_options` attribute access**: The `getattr(rule, "provide_automatic_options", False)` guard in `cli.py` suggests this attribute may not always be present; if Werkzeug's `Rule` interface changes, the `OPTIONS` method could disappear from route listings silently.

## Improvement Suggestions
- Extract `"_automatic_options"` to a module-level constant (e.g. `_AUTO_OPTIONS_ENDPOINT`) used in both `app.py` and `cli.py` to avoid string duplication.
- Add a test that verifies `flask routes` does not list `_automatic_options` endpoints after this change.
- Once Werkzeug 3.2 is released, follow up to tighten the exception catch to `DuplicateRuleError` as noted in the PR description.

## Confidence Score
High

## Summary of changes
This pull request adds `cls.update_template_context` to the list of methods checked in `Flask.__init_subclass__` in `src/flask/app.py`, so subclasses that override it with the old signature are handled in the same way as the other context-aware methods. It also rewrites the docstring of `update_template_context` and adds `versionchanged:: 3.2` notes to many methods stating that they now take `ctx: AppContext` as the first parameter and that the old signature is deprecated until Flask 4.0. In addition, it changes `:internal:` to `:meta private:` in the `finalize_request` docstring and tidies the `process_response` and teardown parameter documentation.

## Identified risks
- Conditional risk, `src/flask/app.py` hunk at `@@ -267,6 +267,7 @@`: the diff shows only the added tuple entry, not the loop body or the `update_template_context` signature. Whether the compatibility wrapper correctly handles this method (for example, the position of `ctx` and the optional `context` argument) cannot be confirmed from the diff.
- Conditional risk, hunk at `@@ -596,12 +597,17 @@`: the new docstring documents `ctx` and `context`, but the visible changed lines do not include the method signature or any call sites. Callers such as template rendering helpers may still pass only `context`, so consistency depends on code outside this diff.
- Documentation-only risk, many hunks: the notes claim the "old signature is deprecated", but the diff does not show the deprecation warning being emitted for each listed method (such as `dispatch_request`, `handle_exception`, `log_exception` or `make_default_options_response`). Only methods in the `__init_subclass__` tuple are visibly covered, and the diff shows only the end of that list, so claims for the others cannot be verified.
- Minor, hunk at `@@ -1060,6 +1094,10 @@` and neighbours: the docstring says the old signature is deprecated, yet the diff shows no tests, changelog entry or upgrade note, so the user-facing behavior change is not visibly validated.
- Minor, hunk at `@@ -1039,7 +1069,11 @@`: replacing `:internal:` with `:meta private:` changes how documentation tools treat the method. This is probably intended, but the effect on the generated documentation is not confirmed.

## Improvement suggestions
- Add or point to tests showing that a subclass overriding `update_template_context` with the old signature (without `ctx`) still works and emits a deprecation warning, mirroring any existing tests for the other wrapped methods.
- Add a `CHANGES.rst` entry for the new deprecation, if it is not already covered by an earlier entry, so that subclass authors can find the migration path.
- Confirm that every method carrying the new `versionchanged:: 3.2` note is covered by the `__init_subclass__` compatibility list, or adjust the notes so they match the actual behavior.
- Document the `ctx` parameter consistently with a `:param ctx:` line in the methods that now lack one (for example `dispatch_request`, `handle_exception` and `preprocess_request`), as was done for `process_response` and the teardown methods.
- Consider dropping the now-removed Flask 0.5 and 0.6 phrasing only if the shortened `versionchanged` notes preserve the same information, which appears to be the case but is worth a quick review.

## Confidence score
Medium

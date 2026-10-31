# Sample review — https://github.com/pallets/flask/pull/5918

> Produced by `claude-review` with the `pr-reviewer` agent on a real PR diff (+56/−30, 5 files).

## Summary

Moves `provide_automatic_options` out of the per-request dispatch check and into routing: each rule with automatic OPTIONS enabled now gets a sibling rule pointing at a shared `_automatic_options` view. `flask routes` hides that internal endpoint and re-adds `OPTIONS` to the displayed method list, and the static view becomes a module-level function instead of a lambda over a weakref.

## Risks

- **high** `src/flask/sansio/app.py:660` — `except Exception: pass` hides every failure while adding the internal rule, not just the duplicate case the description mentions. If `url_map.add` raises for any other reason (invalid `strict_slashes`, a conflicting user rule, an exhausted map), the app keeps `provide_automatic_options == True` with no OPTIONS route: clients get 405, and `flask routes` still prints `OPTIONS` because `cli.py` adds it from the attribute. A silent, self-contradicting state with no traceback.
  ```python
  if provide_automatic_options:
      try:
          self.url_map.add(
              self.url_rule_class(...)
          )
      except Exception:
          pass
  ```

- **medium** `src/flask/cli.py:1080` — `methods = rule.methods or set()` does not copy: `Rule.methods` is the live set, so `methods.add("OPTIONS")` mutates the routing table while the CLI renders it. Harmless for the `flask routes` process, but this code also runs under `CliRunner` inside tests and any embedding that inspects rules afterwards; and it silently drops the `frozenset`-style immutability the rest of the code assumes.
  ```python
  methods = rule.methods or set()
  if getattr(rule, "provide_automatic_options", False):
      methods.add("OPTIONS")
  ```

- **medium** `src/flask/sansio/app.py:645` — the view rule's `methods` no longer contains `OPTIONS` (previously added through `required_methods`). Anything that reads `rule.methods` directly — CORS helpers, API-doc generators, user code building `Allow` headers — now sees a narrower set than the routes actually accept, which is why `cli.py` needs a special case. This is an observable behaviour change and belongs in `CHANGES.rst`, not only in the PR description.

- **low** `src/flask/app.py:363` — `_automatic_options` is registered in `view_functions` for every app, so the name becomes reserved. A user who calls `app.add_url_rule(..., endpoint="_automatic_options", view_func=...)` now hits `AssertionError: View function mapping is overwriting an existing endpoint function` from `add_url_rule` instead of getting their view.

- **low** `src/flask/app.py:1624` — `_options_view` calls `app_ctx._get_current_object()` (a private `LocalProxy` method) and then passes the context into `make_default_options_response(ctx)`. Dispatch already holds the context, and stock Flask's public signature takes no argument, so any subclass or extension overriding `make_default_options_response` breaks on the new call shape without a deprecation path.

## Suggestions

- `src/flask/sansio/app.py:660` — catch `werkzeug.routing.exceptions.DuplicateRuleError` explicitly (guarded with a version check until Werkzeug 3.2 is required) and let everything else propagate; a `try/except` this broad around routing setup will outlive the temporary Werkzeug constraint it was written for.
- `src/flask/cli.py:1080` — use `methods = set(rule.methods or ())` so rendering the CLI never edits the app's routing state.
- `src/flask/app.py:363` — register the internal view under a sentinel key that cannot collide (`_automatic_options` is fine as an endpoint name, but assert it is unused at registration time with a clear message), or attach the view per rule instead of relying on a global endpoint name.
- `src/flask/app.py:1624` — resolve the app once (`ctx = app_ctx._get_current_object()`) only if needed for the signature change; otherwise call `make_default_options_response()` with no argument and keep the documented API intact.
- `tests/test_cli.py:492` — add a case for a rule with `provide_automatic_options=False`: the current assertions only prove that `HEAD`/`OPTIONS` disappear from one screen, not that OPTIONS is still shown when it should be.
- `CHANGES.rst` — add an entry for the `rule.methods` change and the reserved endpoint name; both are visible to extension authors.

## Confidence

**Medium** — the diff is fully visible, but two conclusions depend on code outside it: the current signature of `make_default_options_response` and whether Werkzeug 3.2's `DuplicateRuleError` is already available in the supported version range.

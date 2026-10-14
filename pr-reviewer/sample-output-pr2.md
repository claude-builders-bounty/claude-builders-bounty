# PR Review: pallets/flask#6168 - drop support for Python 3.10

https://github.com/pallets/flask/pull/6168

### Diff overview (computed by `claude-review`, not by the model)

- Files changed: **12** (**+67** / **-433**)
- Changed lines by extension: `.lock` 429 lines, `.py` 50 lines, `.toml` 14 lines, `.rst` 4 lines, `.yaml` 3 lines
- Test files touched: `tests/test_appctx.py`, `tests/test_basic.py`, `tests/test_json_tag.py`, `.github/workflows/tests.yaml`, `tests/test_config.py`

| File | + | - |
|---|---:|---:|
| `uv.lock` | 40 | 389 |
| `tests/test_appctx.py` | 11 | 17 |
| `pyproject.toml` | 4 | 10 |
| `tests/test_basic.py` | 3 | 3 |
| `src/flask/helpers.py` | 1 | 4 |
| `src/flask/sessions.py` | 2 | 2 |
| `tests/test_json_tag.py` | 2 | 2 |
| `.github/workflows/tests.yaml` | 1 | 2 |
| `CHANGES.rst` | 1 | 1 |
| `docs/installation.rst` | 1 | 1 |
| `tests/test_config.py` | 1 | 1 |
| `src/flask/cli.py` | 0 | 1 |

## Summary

The PR drops Python 3.10 support across the project: `requires-python` rises to `>=3.11` in `pyproject.toml` and `uv.lock`, the 3.10 entries leave the CI matrix (`.github/workflows/tests.yaml`) and tox env list, and newly-unlocked 3.11+ idioms are adopted — `datetime.UTC` in `src/flask/sessions.py`, unconditional `BaseExceptionGroup` in `src/flask/helpers.py`, top-level `tomllib` import in `tests/test_config.py`. Most of the 433 deletions are `uv.lock` regeneration (cp310 wheels and `<3.11` dependency markers), and the PR also removes the pyright configuration as part of the `pyproject.toml` cleanup.

## Identified risks

- The changelog entry in `CHANGES.rst` ("Drop support for Python 3.9 and 3.10. :pr:`5730` :pr:`6166`") cites PR 6166, which does not exist in pallets/flask (verified: the API returns 404 for it; this change is PR #6168). As written, the rendered changelog will link to a nonexistent pull request.
- The `uv.lock` regeneration consolidates the resolution markers (`python_full_version < '3.12'` replaces the previous `== '3.11.*'` and `< '3.11'` split), which changes how dependencies resolve for Python 3.11 environments, not just 3.10. A regenerated lockfile cannot be verified line-by-line in review, so correctness for the oldest supported interpreter rests entirely on the 3.11 CI legs passing with the locked environment.
- Removing pyright (the `[tool.pyright]` section and the `["pyright"]` command in the tox `typing` env, both in `pyproject.toml`) is a tooling decision bundled into a version-drop PR whose body is two lines; if it is deliberate it deserves an explicit note, and if not it silently halves the project's static-typing checks.

## Improvement suggestions

- Fix the `:pr:` reference in `CHANGES.rst` to point at this PR (#6168) or at the intended tracking issue.
- Sweep for remaining "3.10" references outside the 12 touched files (for example pre-commit config, README badges, other docs pages) — the diff updates `docs/installation.rst`, but nothing in it shows the rest of the tree was checked.
- Drop the now-obsolete `# noqa: F821` comments left in `tests/test_appctx.py`; they existed for interpreters that lacked the `ExceptionGroup` builtin, which the new floor guarantees.
- Confirm `sys` is still used in `src/flask/helpers.py` after the version branch collapsed — the diff does not touch its import block, and if `sys.version_info` was the only use, the import is now dead.
- State the pyright removal explicitly in the PR description (or split it out) so the decision is visible in project history rather than buried in a metadata diff.

## Confidence: Medium

Every version reference visible in the diff moves consistently (metadata, CI, tox, mypy target, docs, lockfile) and the code modernizations are exactly what the new floor permits, but this is a deliberate public-contract change and the two loose ends above — the dead changelog reference and possible 3.10 mentions outside the diff — cannot be verified from the diff alone.

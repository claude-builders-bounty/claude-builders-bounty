## Summary of changes
This pull request raises the minimum supported Python version for Flask from 3.10 to 3.11 in `pyproject.toml`, `docs/installation.rst`, the changelog in `CHANGES.rst`, and the continuous integration matrix in `.github/workflows/tests.yaml`. It removes compatibility code that is no longer needed, including the version check around `BaseExceptionGroup` in `src/flask/helpers.py`, the `datetime.UTC` alias replacing `timezone.utc` in `src/flask/sessions.py` and tests, and the conditional skip for `tomllib` in `tests/test_config.py`. It also removes the pyright configuration and tox invocation, and regenerates `uv.lock` to drop Python 3.10 wheels and packages such as `tomli` and `exceptiongroup`.

## Identified risks
- Behavior change in `src/flask/helpers.py` (`raise_any` hunk): on Python 3.11 and newer this was already raising `BaseExceptionGroup`, so runtime behavior is unchanged for supported versions. The only effect is that users on Python 3.10 are now excluded rather than receiving the first error, which is consistent with the new `requires-python`.
- Possible lint or type-checking concern in `src/flask/helpers.py`: the `# noqa: F821` comment was removed from the `BaseExceptionGroup` line, and the test file `tests/test_appctx.py` retains `# noqa: F821` on `ExceptionGroup`. Whether ruff flags the undefined name depends on its configured target version, which is not shown in this diff, so this is a conditional risk only.
- The `import sys` line in `src/flask/helpers.py` may now be unused after the version check was removed. The diff does not show whether `sys` is still used elsewhere in that file, so a lint failure cannot be confirmed.
- Dropping pyright (`[tool.pyright]` in `pyproject.toml` and the `pyright` command in the tox typing environment) reduces type-checking coverage. The diff does not explain the reason, and the pull request description is not provided, so intent is unconfirmed. It is also unrelated to the version bump and may surprise downstream users who run pyright against the repository's configuration.
- `uv.lock` was regenerated with large unrelated-looking changes, for example `gha-update`, `httpcore`, and `httpx` losing their `python_full_version >= '3.12'` markers, and `sphinx` collapsing to a single version. These appear to be consequences of lock resolution, but I cannot verify them from the diff alone. Reviewers should confirm the lock file was produced by the project's standard tooling.
- In the continuous integration matrix, the `Development Versions` job moves to Python 3.11, and the `tests-min` job keeps its `python: '3.14'` setting. The diff does not show whether the minimum versions of dependencies, such as `click>=8.1.3`, remain compatible with Python 3.11 only. This is unverified.

## Improvement suggestions
- Add a short note in `CHANGES.rst` or the pull request description explaining why pyright was removed, or split that change into a separate pull request so the version bump stays focused.
- Verify that `import sys` in `src/flask/helpers.py` is still needed and remove it if unused, and confirm the ruff target version is updated (for example `target-version`) so `# noqa: F821` comments on `ExceptionGroup` and `BaseExceptionGroup` are either consistently needed or consistently removed.
- Consider updating the `Programming Language :: Python` classifiers in `pyproject.toml` if any list Python 3.10; the visible context does not show them, so this is worth checking.
- Confirm that the regenerated `uv.lock` was created with the repository's pinned `uv` version and that the continuous integration run passes on all remaining matrix entries (3.11 through 3.14 and PyPy 3.11).

## Confidence score
Medium

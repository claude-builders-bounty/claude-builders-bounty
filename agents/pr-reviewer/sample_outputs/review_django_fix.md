# PR Review: [django/django#17842](https://github.com/django/django/pull/17842)

## Summary
This PR adds support for `DISTINCT ON` expressions in `QuerySet.aggregate()` when using PostgreSQL, allowing callers to write `qs.aggregate(Count("id", distinct=True))` with explicit field targeting instead of the current workaround of using `annotate()` followed by a second queryset. The implementation threads the `distinct_fields` parameter through `SQLAggregateCompiler` and emits the appropriate `DISTINCT ON (...)` SQL clause.

## Identified Risks
- `DISTINCT ON` is a PostgreSQL-only extension; the new code path is not guarded by a database-capabilities check. Running this on SQLite or MySQL will produce a SQL syntax error rather than a clean `NotSupportedError`, which is inconsistent with how other Postgres-only features (e.g., `ArrayField`) are handled.
- The `distinct_fields` parameter is accepted on the base `Aggregate` class but silently ignored by all non-Postgres backends — this could confuse users who test locally on SQLite and see no error, then hit breakage in production on a different backend.
- Error messaging when `distinct_fields` is passed alongside `filter=` is absent; the two options interact in non-obvious ways in PostgreSQL (`FILTER` + `DISTINCT ON` requires a subquery) and the current code does not detect this combination.
- The new `SQLAggregateCompiler` path skips the existing `group_by` deduplication step; complex querysets with multiple annotations may produce incorrect results.

## Improvement Suggestions
- Add a `DatabaseFeatures.supports_distinct_on_aggregate` capability flag and raise `NotSupportedError` in `Aggregate.as_sql()` when the flag is `False`.
- Expand the test matrix to include at least one test on a non-Postgres backend (SQLite) confirming a clear error is raised.
- Add a test for the `distinct_fields` + `filter=` combination and either document the limitation or implement the required subquery rewrite.
- The PR description references ticket #34513 but the commit message does not — include `Refs #34513` in the commit message to keep the ticket linkage in `git log`.
- Consider extracting the `DISTINCT ON` clause rendering into a helper method on `SQLAggregateCompiler` so it can be unit-tested in isolation.

## Confidence Score
**Medium** — The core logic is clear and the happy-path tests pass, but the lack of cross-backend guards and the untested `FILTER` interaction lower confidence that this is production-safe without further review from the Django ORM core team.

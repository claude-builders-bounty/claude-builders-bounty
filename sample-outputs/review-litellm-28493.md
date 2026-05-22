# PR Review: fix(prometheus): emit org_id and org_alias on litellm_llm_api_failed_requests_metric
**Repository:** [BerriAI/litellm](https://github.com/BerriAI/litellm)
**PR:** [#28493](https://github.com/BerriAI/litellm/pull/28493)

---

## Summary

This PR fixes a bug where organization ID and alias labels were missing from Prometheus failure metrics (`litellm_llm_api_failed_requests_metric`). The fix extracts the org alias from logging metadata, passes both org ID and alias to the label values, and adds the failure metric to the org-labeled metrics set.

## Risks

- No significant risks identified.

The changes are additive and well-isolated, with proper test coverage for both success and edge cases. The fix addresses missing data rather than changing existing behavior.

## Suggestions

- **Test coverage looks comprehensive** — the two new tests in `test_prometheus_user_team_metrics.py` cover both the happy path (org context present) and edge case (no org context).
- **Good defensive programming** — the code properly handles `None` values for org fields when they're absent from metadata.
- **Well-structured fix** — addresses both the data extraction issue in `async_log_failure_event` (lines 1640-1653 in prometheus.py) and the metric configuration issue by adding the failure metric to `_org_label_metrics` (line 657 in prometheus.py types).

## Confidence

**High**

The changes are straightforward, well-tested, and follow the existing patterns in the codebase. The bug was clearly identified (missing org label extraction and metric registration), and the fix directly addresses both root causes without side effects.

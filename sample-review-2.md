# Review: rohitdash08/FinMind#776 — feat(budgets): category overspend early warning system

## Summary
This PR introduces a category overspend early warning system by adding a `BudgetLimit` model and a full CRUD + warnings API (`/budgets`) on the backend, wiring it up to a new `budgets.ts` API client on the frontend, and surfacing dismissible warning banners on the Dashboard and a live budget tracker on the Budgets page. Static mock data in `Budgets.tsx` is replaced with real API-driven data, and a migration (`003_add_budget_limits.py`) along with integration tests are included.

## Risks
- **N+1 query in `/budgets` and `/warnings`**: For each `BudgetLimit` row, a separate `db.session.get(Category, ...)` call is made inside a loop. With many budget lines this will produce N+1 database queries; categories should be batch-loaded or joined.
- **UniqueConstraint broken for `category_id = NULL`**: SQL treats `NULL != NULL`, so the unique constraint `(user_id, category_id, month)` will not prevent duplicate "Total" (category_id=NULL) budgets in most databases (PostgreSQL, SQLite). The `filter_by(..., category_id=None)` upsert lookup in `create_budget` may also silently create duplicates depending on the ORM/driver.
- **Silent error suppression**: Both `catch { /* ignore */ }` blocks in `Budgets.tsx` (`load` and `handleSave`) swallow all errors with no user feedback. A failed save will silently do nothing, leaving the user confused.
- **Toasts fired on every `load()` call**: In `Budgets.tsx`, every call to `load()` (including the one after saving a budget) re-fires destructive toast notifications for critical/over categories, which can be spammy and disorienting.
- **`currentMonth` re-computed each render**: `new Date().toISOString().slice(0, 7)` in `Budgets.tsx` is a plain `const` inside the component body, not a `useState` or `useMemo`, so it will be a consistent string but could theoretically tick over mid-session without the component reacting; it should at minimum be a stable reference.
- **No loading skeleton / error state in Budgets page**: The `loading` flag only replaces metric values with `'...'` strings; the category list renders nothing useful while loading and errors are silently ignored, degrading UX.
- **`pct_used` is a raw float displayed without rounding in the UI**: `{w.pct_used}%` in Dashboard warnings could display values like `95.0%` or `110.00000000000001%` depending on floating-point arithmetic; the backend rounds to 1 decimal but the frontend should format it defensively.
- **Progress bar color override via dynamic Tailwind class**: `` `[&>div]:${statusColor[w.status]}` `` uses a dynamically assembled class string. Tailwind's JIT compiler will not detect these classes at build time, meaning the colored progress indicators will likely not render in production.
- **Missing test coverage for NULL category (total budget) and upsert path**: `test_budgets.py` only tests per-category budgets; the "Total (all categories)" budget path and the update-existing-limit flow are not covered.
- **No authorization check on category ownership**: `create_budget` accepts any `category_id` without verifying it belongs to the authenticated user, potentially allowing cross-user category references.

## Suggestions
- **Batch-load categories**: Use a single join or `IN` query (e.g., `db.session.query(Category).filter(Category.id.in_([...]))`) before the loop to eliminate N+1 queries in both `list_budgets` and `budget_warnings`.
- **Handle NULL uniqueness explicitly**: Add a partial unique index or an application-level guard (e.g., `filter(BudgetLimit.category_id.is_(None))`) specifically for the total-budget row to reliably enforce one total budget per user per month.
- **Surface errors to users**: Replace `catch { /* ignore */ }` with `toast({ title: 'Failed to load budgets', variant: 'destructive' })` and similar so failures are visible.
- **Deduplicate toast notifications**: Track which warnings have already been toasted (e.g., via a ref or by

# Recorded fixtures

These fixtures were recorded with `gh api` from `microsoft/vscode` for the UTC
range `2026-10-08T17:00:00+00:00..2026-10-15T17:00:00+00:00`.

- `commits-page-1.json`: 100 records returned by page 1 with `per_page=100`.
- `commits-page-2.json`: the first 3 records from the real page-2 response.
- `prs-page-1.json`: 100 records returned by page 1 with `per_page=100`.
- `prs-page-2.json`: the first 3 records from the real page-2 response.
- `issues-page-1.json`: the first 10 records from the real page-1 response.

The reduced page-2 and issue fixtures keep the repository size bounded while
retaining real API shapes and values. Page 1 remains at 100 records so the
workflow's own pagination logic must request page 2.

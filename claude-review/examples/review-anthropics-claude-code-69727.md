# PR Review: anthropics/claude-code#69727 — fix(hookify): match file rules against Write tool content

## Summary
This PR fixes a bug in the hookify plugin's rule engine where file content matching didn't work for the Write tool. The `_extract_field` method now correctly falls back to the `content` field when `new_string` is not available, matching the Write tool's input format.

## Risks
- The change is minimal and well-scoped — only one line is modified
- The fallback chain (`new_string` → `content`) preserves backward compatibility with Edit tool inputs
- No edge cases identified where this could break existing behavior

## Suggestions
- Consider adding a comment or docstring explaining the Write vs Edit tool input differences for future maintainers
- Could add a unit test specifically for Write tool field extraction to prevent regressions
- The `or` fallback pattern is clean but worth noting it treats empty string the same as missing key

## Confidence
High

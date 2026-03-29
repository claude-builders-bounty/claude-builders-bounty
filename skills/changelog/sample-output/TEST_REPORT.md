# Sample Output — Test Report

## Test Environment

- **Repository:** `expressjs/express` (https://github.com/expressjs/express)
- **Date:** 2026-03-29
- **Tool:** `changelog.py` (Python cross-platform version)
- **Command:** `python3 changelog.py --repo /tmp/express-test --output CHANGELOG.md --all`
- **Commits tested:** Last 30 commits (shallow clone)
- **Result:** ✅ SUCCESS

## Results Summary

| Category | Entries |
|----------|---------|
| Added    | 2       |
| Fixed    | 3       |
| Changed  | 25      |
| **Total** | **30** |

## Sample Output

See [`CHANGELOG.md`](./CHANGELOG.md) for the full output.

## Notes

- The tool correctly categorized `feat:` commits as **Added**
- `fix:` commits were properly categorized as **Fixed**
- `docs:`, `chore:`, `build(deps):`, `test:` commits correctly categorized as **Changed**
- Merge commits were automatically skipped
- The output follows the Keep a Changelog 1.0.0 format
- Works correctly with shallow clones (depth=30)

## Other Testing

Also tested on:
- `claude-builders-bounty` (this bounty board itself): ✅ 2 commits categorized
- Both bash (`changelog.sh`) and Python (`changelog.py`) versions confirmed working

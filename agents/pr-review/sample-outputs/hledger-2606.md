## PR Review: fix: handle empty journal in close command instead of crashing (fixes #2409)
**Confidence Score:** High

### Summary
This PR handle empty journal in close command instead of crashing (fixes #2409) The changes are predominantly test (1 files), other (2 files) and represent a small change set. The PR can be reviewed at https://github.com/simonmichael/hledger/pull/2606. The changes appear well-scoped and low-risk.

### Changes by File
| File | + | - | Type |
|------|---|---|------|
| `b/Justfile` | 2 | 0 | other |
| `b/hledger/Hledger/Cli/Commands/Close.hs` | 3 | 1 | other |
| `b/hledger/test/close.test` | 4 | 0 | test |

### Identified Risks
No significant risks detected.

### Improvement Suggestions
- 💡 Line too long in `b/Justfile` (170 chars) — consider wrapping

### Detailed File Analysis

#### `b/Justfile`
Added 2 line(s)

#### `b/hledger/Hledger/Cli/Commands/Close.hs`
Added 3 line(s)
Removed 1 line(s)

#### `b/hledger/test/close.test`
Added 4 line(s)

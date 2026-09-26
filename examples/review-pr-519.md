# Sample review — PR #519 (ubiquity/ai.ubq.fi)

Command:
```bash
claude-review --pr https://github.com/ubiquity/ai.ubq.fi/pull/519
```

Output:

## Review of PR #519

### Summary
Hardens the benchmark fixture rollback so a command that removes read or traverse permissions can no longer abort enforcement. Snapshot entries that become unreadable mid-walk are recorded as present-but-unreadable (`content: null`) instead of failing the whole snapshot, and `runVerification`/`evaluateOracle` now convert write-scope violations into failed outcomes (`verification_failed`) rather than throwing and killing the batch.

### Risks
- `_recoverAncestorAccess` performs `chmod(finalMode | 0o700)` on every real ancestor before restoring each entry; on platforms where the running user does not own the directory (or a mount enforces its own ACL), the chmod may succeed but the restore write can still fail later, leaving a partially restored workspace that is reported as a `write_scope` violation with incomplete state.
- `expected.content ?? new Uint8Array(0)` restores an empty file when the saved bytes were unreadable — if the command truncated the file before removing read bits, the rollback cannot recover the original bytes, only the mode; the test suite documents this as a last resort, but callers relying on content equality will see a difference that is not flagged.
- The deepest-first directory-mode pass uses `b.split("/").length`; paths containing symlink-resolved segments or absolute prefixes are compared consistently here, but any future change to how `rel` is built (for example Windows path separators) would silently change the ordering.

### Improvement suggestions
- **Restore verification** — after the final mode pass, re-read a small marker (e.g. the first bytes of a restored protected file) and emit a distinct warning/flag when the content could not be recovered, instead of silently writing an empty file (`benchmarks/fixture.ts`, `_enforceWriteScope`).
- **Ownership guard** — in `_recoverAncestorAccess`, skip the collapse to `0o700` when the directory is not owned by the current user (or when `finalMode` already contains execute bits), and document the ACL caveat in the doc comment.
- **Path normalization** — sort directory modes with a normalized depth using the platform separator, or add an invariant/assertion that entries are relative forward-slash paths, to keep the ordering stable across OSes (`benchmarks/fixture.ts`, final loop).

### Confidence
**High** — the change is self-contained, the permission scenarios are captured by the new `chmod 000` and read-only-parent tests, and the verification error handling is now covered at both the `runVerification` and `runOne` layers.
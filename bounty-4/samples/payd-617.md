# Sample review — Protocol-Guild/PayD #617

Source PR: https://github.com/Protocol-Guild/PayD/pull/617  
Reviewed head: `9050da261cec5ea97c49bfe40ff9b631ee5da17c`

## Summary
This PR reuses the claimed PostgreSQL client while recording schedule execution, lets `ScheduleService.updateAfterExecution` participate in the caller's transaction, and removes the previous unconditional unlock path. It commits execution history and schedule state before performing an owner-qualified lock release, reducing the chance that a different executor's lock is cleared.

## Risks
- Execution history/state are committed before the lock-release statement runs. If that final `UPDATE ... WHERE locked_by = $podId` fails or returns no row, the schedule is durably advanced but remains locked; a stale-lock recovery path must not interpret that retained lock as proof the work still needs to execute or duplicate payment/execution can occur.
- A successful schedule execution whose final unlock fails falls into the `recordError` path and increments `failureCount`, so operational metrics can report a failure even though the execution and state transition were already committed.
- `recordExecution` now requires a caller-owned `PoolClient`. Any call site not shown in this diff that invokes the public method directly must be updated or it will fail at compile/runtime integration.

## Improvement suggestions
- Keep the owner-qualified unlock in the same transaction as execution-history and schedule-state updates, or make stale-claim recovery explicitly consult the committed execution generation before retrying work.
- Track execution outcome separately from finalization/unlock outcome so metrics and alerts do not relabel a committed successful execution as a business failure.
- Audit all `recordExecution` call sites after the signature change and, if it is intentionally internal-only, narrow its visibility so future callers cannot omit claim-client ownership.

## Confidence
High

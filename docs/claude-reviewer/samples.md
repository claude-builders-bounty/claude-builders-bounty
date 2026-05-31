# Sample Outputs

These samples were generated with live GitHub pull requests.

## Sample 1

Command:

```bash
python claude-review --pr https://github.com/archestra-ai/archestra/pull/5144
```

Output:

```markdown
## Summary

This PR for https://github.com/archestra-ai/archestra/pull/5144 changes 5 file(s), with 128 additions and 14 deletions across 14 diff hunk(s).
The touched areas look like application code, tests; primary files include `platform/backend/src/routes/chat/context-compaction.ts`, `platform/backend/src/routes/chat/routes.ts`, `platform/frontend/src/lib/chat/global-chat.context.test.tsx`, `platform/frontend/src/lib/chat/global-chat.context.tsx`, `platform/shared/chat.ts`.

## Identified Risks

- No obvious static risk patterns were detected in the diff.

## Improvement Suggestions

- Ask a maintainer familiar with `platform/backend/src/routes/chat/context-compaction.ts` to sanity-check the main behavior change.
- Confirm user-facing behavior against the issue acceptance criteria, not only static checks.

## Confidence: High
```

## Sample 2

Command:

```bash
python claude-review --pr https://github.com/algora-io/algora/pull/299
```

Output:

```markdown
## Summary

This PR for https://github.com/algora-io/algora/pull/299 changes 2 file(s), with 4 additions and 2 deletions across 2 diff hunk(s).
The touched areas look like project files; primary files include `lib/algora_web/endpoint.ex`, `lib/algora_web/live/org/bounties_live.ex`.

## Identified Risks

- No obvious static risk patterns were detected in the diff.

## Improvement Suggestions

- Ask a maintainer familiar with `lib/algora_web/endpoint.ex` to sanity-check the main behavior change.
- Confirm user-facing behavior against the issue acceptance criteria, not only static checks.

## Confidence: High
```

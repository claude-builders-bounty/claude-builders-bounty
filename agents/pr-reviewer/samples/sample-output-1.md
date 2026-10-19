## Summary
This PR fixes the bug where deleting the old primary email in Settings → Profile, after promoting a verified secondary email, brought the old email back in the `SecondaryEmail` table. The frontend now sends an explicit retain or delete marker (`id: 0`) for the old primary. The backend only repurposes the promoted `SecondaryEmail` row to hold the old primary when the user kept it, and otherwise deletes that row. The backend also clears `EventType.secondaryEmailId` for event types bound to the promoted email, so they fall back to the new primary. The direction is sound, but the backend now treats an absent marker as "delete", which changes behavior for any caller other than this form.

## Risks
- **Behavior change for non-UI callers.** Previously the swap was unconditional. Now the old primary is kept only if it is explicitly present and not deleted (`!isOldEmailExplicitlyDeleted && isOldEmailExplicitlyRetained`). Any caller that doesn't send the marker (API or platform clients, older cached frontends, tests) silently loses the old email, and the promoted row is deleted. Silent loss of a verified address is the harder failure to notice than the original bug.
- **Possible duplicate entries on the frontend.** If the form's `secondaryEmails` already contains the old primary (that is how `isOldPrimaryRetained` can be true), the new `updatedEmails.push({ id: 0, ... })` may duplicate an entry already in `updatedEmails`. I couldn't see how `updatedEmails` is built, so this needs checking. The backend ignores `id <= 0`, which hides it, but the payload is still redundant.
- **Non-atomic multi-step writes.** `deleteMany` of the promoted row, then the `secondaryEmail` deletes and updates, then `eventType.updateMany` all run as separate queries with no transaction. A failure midway leaves partial state. Examples are a promoted row deleted with event types still bound, or the user already switched to the new primary but the swap not applied.
- **FK behavior on delete is unverified.** If `EventType.secondaryEmailId` is `onDelete: Restrict` (or the default), the `deleteMany` of the promoted row throws before event types are disconnected. If it is `SetNull`, the later `updateMany` is redundant in the delete branch. The ordering is wrong in the first case and unnecessary in the second.
- **Swap branch ordering.** The swap pushes a second entry with `id: secondaryEmail.id`. If the form payload also still contains that id as non-deleted (the new primary), two modifications target the same row, and which one wins depends on queue order.
- **Masked data errors.** `keyedSecondaryEmailsFromDB[updated.id]?.emailVerified ?? null` and `?.email` replace a hard failure with a silent `null` for missing rows. A row the user doesn't own (filtered by `userId`) would now be reset to unverified instead of failing visibly.
- **Unverified-email path.** The frontend now sends `{ id: 0, isDeleted: true }` for the old primary whenever the primary changes, including when the new address is unverified and goes through the verification flow. This is harmless today because of the `id > 0` filter, but the intent differs from the verified-promotion case.
- **Possibly useful old-email data is dropped.** `emailVerified: null` is sent on the delete marker, and the retain marker uses `user.emailVerified?.toString()`. The backend recomputes verification, so this is likely fine, but the two markers are inconsistent.
- **No tests.** No tests are included for the promote-and-keep, promote-and-delete, and event-type-disconnect paths. The PR body is also truncated, so the last bullet ("Disconnect se...") is unreadable.

## Suggestions
- Make the "neither deleted nor retained" case preserve the old primary (the previous default), and delete the promoted row only on an explicit `isDeleted: true`. That keeps API and older-client behavior intact.
- Wrap the promoted-row delete or swap, the secondary-email writes, and the `eventType.updateMany` in a single `prisma.$transaction`.
- Check the Prisma schema for the `EventType.secondaryEmailId` relation's `onDelete`. Run the event-type disconnect before the delete, or rely on `SetNull` and drop the redundant update.
- Dedupe the `id: 0` marker on the frontend, for example by skipping the push when `updatedEmails` already has the old primary's email.
- Extract the repeated case-insensitive comparison (`e.email.toLowerCase() === user.email.toLowerCase()`) into a small helper or a precomputed `oldEmailLower`. Normalize once on both sides.
- Replace the `?.` and `?? null` fallbacks with an explicit check that throws or skips and logs when a row is missing.
- Add tests for the three scenarios above, plus one where the payload omits the old email entirely.

## Confidence
Medium. The logic is readable and the intent is clear, but I couldn't see `updatedEmails`, the Prisma relation, or the zod input schema, so the duplicate-entry and FK concerns are unconfirmed.

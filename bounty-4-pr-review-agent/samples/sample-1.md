## Summary
This PR adds guest availability checking when a host reschedules a booking in cal.com. It fetches attendee busy times by resolving attendee emails to Cal.com users, querying their existing bookings, and merging those busy times into the host's availability view — so the reschedule calendar only shows mutually available slots.

## Risks
- **Silent error swallowing**: The `catch` block in `_getGuestBusyTimesForReschedule` returns `[]` without logging the error. A database outage or bug would silently degrade to showing all slots with no diagnostic trail, making production issues hard to detect.
- **Missing `rescheduledBy` falls through to guest-check path**: When `rescheduledBy` is `null`/`undefined` (backwards compat), the code skips the host-check gate and always fetches guest busy times. This means attendee-initiated reschedules on older clients (that don't pass `rescheduledBy`) will unnecessarily restrict slots — a behavioral regression for existing deployments.
- **OR query with empty array edge case**: In `findByUserIdsAndDateRange`, if only `userIds` is populated and `userEmails` is empty (or vice versa), the `OR` array gets one element. While Prisma handles this, a single-element `OR` is semantically unnecessary and could confuse future maintainers.
- **No rate limiting or pagination on guest booking queries**: `findByUserIdsAndDateRange` has no limit on returned rows. A guest with thousands of bookings in the date range could cause performance degradation.
- **Import reordering in `useEvent.ts`, `useSchedule.ts`, `types.ts`**: These are cosmetic changes mixed into a feature PR, inflating the diff and making review harder. Risk is low but violates single-responsibility commit hygiene.

## Suggestions
- **Log the caught error** in `_getGuestBusyTimesForReschedule` before returning `[]` — at minimum `log.warn("Failed to fetch guest busy times for reschedule", { rescheduleUid, error })`. The `withReporting` wrapper may not catch errors inside a try/catch.
- **Consider defaulting to skip guest-check when `rescheduledBy` is missing** rather than defaulting to check. The current backwards-compat behavior (treating missing `rescheduledBy` as host-reschedule) could restrict slots for attendee reschedules on older clients. A safer default would be to only activate guest blocking when `rescheduledBy` is explicitly the host.
- **Add a `take` limit** to `findByUserIdsAndDateRange` (e.g., `take: 500`) to bound query results and prevent performance issues with heavily-booked guests.
- **Split import reordering into a separate commit** to keep the feature diff clean and reviewable.
- **Add the `findByEmails` and `findByUserIdsAndDateRange` methods to their respective repository interfaces** (`IBookingRepository`, etc.) if those interfaces exist, to maintain the contract pattern used elsewhere in the codebase.

## Confidence
**High**

The PR is well-structured with thorough tests (30 tests, 631 lines), clean repository-pattern usage, and correct handling of edge cases (COLLECTIVE skip, non-Cal guests, dedup, case-insensitive emails, excludeUid at DB level). The risks identified are real but bounded.

---
*Automated review by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty)*

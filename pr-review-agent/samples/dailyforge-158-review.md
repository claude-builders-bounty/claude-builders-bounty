## 📋 PR Review — DailyForge #158: fix: add interval overlap detection for task scheduling

### Summary
This PR adds time interval overlap detection to the task scheduling system in DailyForge's RoutineBuilder component. It introduces a `hasOverlap` function that checks whether a new task's time slot conflicts with existing scheduled tasks on the same day, preventing users from accidentally double-booking time slots in their routines. The change also includes corresponding test coverage in `RoutineBuilder.test.jsx`.

### ⚠️ Identified Risks
- **Edge case: boundary overlap** — The `hasOverlap` function uses strict inequality (`newStart < existingEnd && newEnd > existingStart`) which correctly handles most overlaps, but tasks that start exactly when another ends (e.g., 10:00-11:00 and 11:00-12:00) are allowed. This may be intentional but worth documenting as the expected behavior.
- **Missing server-side validation** — The overlap check is only on the frontend (`RoutineBuilder.jsx`). If the API endpoint `/routines` accepts overlapping items directly, a user could bypass this validation via direct API calls. Consider adding overlap validation in the backend as well.
- **Time format dependency** — The overlap detection assumes time values are comparable as strings (e.g., "09:00" < "10:00"). This works for 24-hour HH:MM format but will silently break if the app ever supports 12-hour format or different locales.
- **User feedback UX** — When overlap is detected, an `alert()` is used. This blocks the UI thread and provides a poor UX. Consider using a toast notification or inline error message instead.

### 💡 Improvement Suggestions
- **Extract overlap logic to a utility module** — The `hasOverlap` function (lines ~30-40 in the diff) could be moved to a shared `src/utils/time.js` file and exported with unit tests. This makes it reusable across components and easier to test in isolation.
- **Add visual conflict indicator** — Instead of only alerting on save, consider showing a visual indicator (e.g., red highlight) on conflicting time slots in the weekly grid as the user drags tasks.
- **Internationalize time parsing** — Wrap time comparisons in a utility like `parseTime(startTime)` to handle locale-aware formats. Use `dayjs` or `date-fns` if already in the project dependencies.
- **Test coverage expansion** — The test file adds overlap test cases, but should also test: (a) edge case where tasks abut but don't overlap, (b) multiple existing tasks with one overlap, (c) empty task list returns no overlap.

### 🎯 Confidence Score
**High** — The diff is focused and self-contained (single component + tests). The overlap logic is straightforward and well-tested, though the lack of server-side validation is the most notable gap.

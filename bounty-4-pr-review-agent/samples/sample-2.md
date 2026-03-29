## Summary
This PR removes direct antd imports from settings pages in the Highlight frontend, replacing them with `@highlight-run/ui` equivalents (`ComboboxSelect`, `Select`, `SwitchButton`, `Callout`, `Tooltip`) and native HTML elements. The migration covers workspace settings, project settings, and team management pages, aligning with issue #8635's goal of eliminating antd dependencies from the settings scope.

## Risks
- **ComboboxSelect option shape change**: The `githubOptions` mapping changed from `{id, label, value}` to `{key, render}`. If `ComboboxSelect` expects additional fields (e.g., `value` for form submission), the selected repo identifier may not propagate correctly. The old code displayed `repo.name.split('/').pop()` but submitted the stripped `repo_id` — verify the new `key`/`render` contract preserves this distinction.
- **Display value regression in GitHubSettingsModal/GitHubEnhancementSettingsForm**: The old antd `Select` showed `formState.values.githubRepo?.split('/').pop()` as the display text; the new code passes the full `formState.values.githubRepo ?? ''` as `value`. If `ComboboxSelect` displays the raw value rather than matching it to an option's `render`, users will see a full repo path instead of the short name.
- **Select `onValueChange` contract difference**: `ErrorFiltersForm` and `ErrorSettingsForm` switched from `onChange((values: string[]) => ...)` to `onValueChange((items: {name, value}[]) => ...)`. If the UI `Select` ever emits items with `value` differing from what the user typed (e.g., trimming, lowercasing), the regex patterns or JSON paths could silently change.
- **Native `<input>` loses built-in validation/styling**: Replacing `@components/Input` with a raw `<input>` plus hand-rolled CSS may miss focus-visible outlines, dark-mode tokens, or accessibility attributes that the wrapper provided.
- **CSS file missing trailing newline**: `FieldsForm.module.css` ends without a newline (`No newline at end of file`), which can cause noisy diffs later.
- **`handleToggle` logic change**: The old checkbox used `event.target.checked`; the new toggle infers state from `autoJoinDomains.length === 0`. If `SwitchButton` fires `onChange` before the domain state updates (or fires on mount), the toggle could invert unexpectedly.

## Suggestions
- **Verify `ComboboxSelect` option contract**: Confirm that `{key, render}` is the correct shape by checking the component's TypeScript interface. If it also needs a `value` field, add it explicitly to avoid silent failures.
- **Restore short-name display for GitHub repo selectors**: Either pass the split-last-segment value or confirm `ComboboxSelect` automatically resolves `value` → `render` via the options list.
- **Add trailing newline** to `FieldsForm.module.css`.
- **Use design-system CSS tokens consistently**: The hand-rolled `.dangerInput` and `.fieldInput` styles duplicate each other almost identically. Extract a shared `.settingsInput` class or, better, check if `@highlight-run/ui` already exposes a `TextInput` component.
- **Guard `handleToggle` with the `SwitchButton`'s actual checked value**: Accept the new checked state as a parameter (`onChange={(checked) => ...}`) rather than inferring it from domain length, to avoid race conditions.
- **Consider keeping `disabled` prop on `ComboboxSelect`**: The `GitHubEnhancementSettingsForm` passes `disabled={disabled || testLoading}` but `GitHubSettingsModal` dropped it — verify this is intentional.

## Confidence
**Medium**

The diff is straightforward component swaps, but without access to the `@highlight-run/ui` component interfaces I cannot confirm the option shapes and callback signatures are fully correct — the display-value and toggle-logic risks warrant manual verification.

---
*Automated review by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty)*

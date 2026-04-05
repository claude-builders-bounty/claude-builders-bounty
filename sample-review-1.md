# Review: rohitdash08/FinMind#775 — feat(locale): locale-aware date, currency & number formatting

## Summary
This PR introduces a locale-aware formatting layer (`app/src/lib/locale.ts`) that centralises date, currency, and number formatting using the `Intl` APIs, driven by a user-selected locale stored in `localStorage`. The existing `formatMoney` in `currency.ts` is refactored to delegate to the new `formatCurrency` helper, eliminating duplicated `Intl.NumberFormat` logic. A locale picker is added to the Account settings page with a live preview, and the feature is covered by a new unit-test file.

## Risks
- **SSR / non-browser environments**: `getLocale()` and `setLocale()` call `localStorage` and `window` directly at the module level with no guard, which will throw in any server-side or worker context (e.g., Next.js SSR, Vite SSW, test environments without jsdom configured).
- **No locale validation in `setLocale`**: Any string (e.g., a malformed value from a future API or manual `localStorage` edit) is accepted and stored without checking against `SUPPORTED_LOCALES`, potentially causing silent `Intl` errors at runtime.
- **Silent `Intl` fallback hides bugs**: The `catch` block in `formatCurrency` swallows all errors and falls back to a plain string, making invalid currency codes or locale issues invisible in production monitoring.
- **`formatDate` with string input timezone ambiguity**: `new Date('2026-01-15')` parses as UTC midnight, which can render as the previous day in negative-UTC-offset locales — a classic off-by-one date bug, especially visible in the Account preview.
- **Locale change does not trigger React re-renders globally**: `setLocale` fires a DOM `locale_changed` event, but no component outside `Account.tsx` listens to it. Components displaying formatted values elsewhere will show stale formatting until remounted or refreshed.
- **`formatCurrency` still calls `getCurrency()` from `auth`**: This retains a hidden dependency on the auth module inside `locale.ts`, creating a layering violation — a "locale" utility should not know about auth state.
- **`minimumFractionDigits: 2` hard-coded for all currencies**: Currencies like JPY have zero decimal places by convention; forcing two decimals (e.g., `¥1,234.00`) is incorrect and may confuse users.
- **Test coverage gaps**: `formatDate` tests only assert `.toContain` on partial strings, making them locale-engine-dependent and potentially brittle across Node versions or CI environments with different ICU data.

## Suggestions
- **Guard browser globals**: Wrap `localStorage` and `window` accesses with `typeof window !== 'undefined'` checks, or inject them as dependencies to support SSR and improve testability.
- **Validate locale on `setLocale`**: Check the supplied value against `SUPPORTED_LOCALES` (or use `Intl.supportedValuesOf` where available) and throw or warn on invalid input.
- **Decouple auth from locale**: Pass `currencyCode` as a required parameter to `formatCurrency` and remove the `getCurrency()` call from `locale.ts`; let call-sites resolve the default currency.
- **Respect currency fraction digits**: Drop the hard-coded `minimumFractionDigits`/`maximumFractionDigits: 2` and let `Intl.NumberFormat` use the currency's natural fraction digits, or use `Intl.NumberFormat(locale, { style: 'currency', currency }).resolvedOptions()` to detect the correct value.
- **Propagate locale changes via React context**: Expose locale state through a `LocaleContext` / `useLocale` hook so all consuming components re-render automatically when the locale changes, rather than relying on a manual DOM event.
- **Fix string-to-Date parsing**: Append `T00:00:00` (local) rather than relying on the ISO date-only form, or use a date library, to avoid the UTC-midnight off-by-one issue.
- **Improve test assertions**: For `formatDate`, prefer snapshot tests or locale-specific expected strings rather than loose `.toContain` checks to catch regressions across ICU data updates.
- **Persist locale to the user profile**: Currently locale is client-only (`localStorage`). Consider saving it server-side alongside currency so it ro

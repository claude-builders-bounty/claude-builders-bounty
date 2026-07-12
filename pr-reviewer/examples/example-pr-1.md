### Summary of changes
This PR introduces a new `Button` component to the UI library, featuring configurable variants (`primary`, `secondary`, and `danger`) and sizing options. It also includes corresponding unit tests for the component and updates the Storybook documentation to showcase its usage.

### Identified risks
*   **Accessibility:** The `Button` component currently lacks explicit `aria-label` propagation, which might impact screen reader users if the button text is missing or an icon is used alone.
*   **Performance:** The dynamic CSS-in-JS classes recompute on every render, which might introduce slight performance overhead in lists with many buttons.
*   **Compatibility:** It introduces a breaking change by replacing the legacy `LegacyButton` import across 12 files without providing a backward-compatibility layer.

### Improvement suggestions
*   Pass standard HTML attributes like `aria-label`, `disabled`, and `type` directly to the underlying `<button>` element via rest props (`...props`).
*   Memoize the style calculations or use static CSS classes instead of dynamic injection to improve render performance.
*   Consider providing a codemod or a temporary alias for `LegacyButton` to ease the migration for consumers of the library.

### Confidence score
High. The implementation is straightforward and follows React best practices, but the accessibility and migration paths need to be addressed.

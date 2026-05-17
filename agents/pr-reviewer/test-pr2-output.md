# PR Review: fix: add contextual empty-state copy for gallery tabs

**PR:** [https://github.com/Abhash-Chakraborty/Find/pull/121](https://github.com/Abhash-Chakraborty/Find/pull/121)
**Author:** @banthevaishnavi  
**Changes:** +96/-11 across 1 files

---

## Review

### Summary
This PR introduces contextual empty-state messaging for the Gallery tabs based on the active filter and liked-only toggle. It replaces the generic "No images found" message with tab-specific titles and subtitles for All, Indexed, Processing, and Failed states, improving user clarity. The implementation is scoped to empty-state behavior only and achieves its goal of providing clearer feedback without altering existing layout logic.

### Identified Risks
- **Risk 1: Missing empty state for future filters** – The `getGalleryEmptyState` function uses a hardcoded switch on `"all" | "indexed" | "processing" | "failed"`. If new filter values are added later (e.g., `"archived"`), the function will fall through to the `failed` branch due to the `if (likedOnly)` check, potentially showing incorrect messaging.
- **Risk 2: Liked-only logic duplication** – The liked-only check is repeated inside each filter branch, leading to code duplication. If the liked-only logic needs to change (e.g., adding a new filter), all branches must be updated, increasing maintenance risk.
- **Risk 3: No handling for empty data while loading** – The `emptyGalleryCopy` is computed only when `data` exists and `data.items.length === 0`. If `data` is `undefined` (initial loading state), no empty state is shown, which is correct. However, if the API returns an empty array for a non-empty state (e.g., error), the empty state may appear incorrectly. This is a minor edge case but worth noting.

### Improvement Suggestions
- **Suggestion 1: Use a lookup object instead of if-else chain** – Replace the `if/else` chain with a lookup object keyed by filter and liked-only status. This makes the code more declarative, easier to extend, and reduces duplication. Example:
  ```typescript
  const EMPTY_STATE_MAP: Record<GalleryStatusFilter, {
    default: { title: string; subtitle: string | null; showUploadLink: boolean };
    likedOnly: { title: string; subtitle: string | null; showUploadLink: boolean };
  }> = {
    all: {
      default: { title: "No images found", subtitle: null, showUploadLink: true },
      likedOnly: { title: "No liked images", subtitle: "...", showUploadLink: false },
    },
    // ... other filters
  };
  ```
- **Suggestion 2: Extract liked-only logic into a helper** – Create a small helper function `getLikedOnlyEmptyState(filter)` that returns the liked-only variant for a given filter. This avoids repeating the `if (likedOnly)` check in every branch and centralizes the logic.
- **Suggestion 3: Add a fallback for unknown filters** – Include a `default` case in the `getGalleryEmptyState` function that returns a generic empty state (e.g., `"No images found"` with upload link) to handle unexpected filter values gracefully.

### Confidence Score
**High**

The change is well-scoped, the logic is straightforward, and the diff is clean. The only risks are related to future maintainability rather than correctness of the current implementation. The suggestions are optional improvements to reduce duplication and improve extensibility.
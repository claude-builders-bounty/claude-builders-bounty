# Changelog

## [svelte@5.56.10] - 2026-08-22

### Added

- Export RenderOutput, SyncRenderOutput, Csp and Sha256Source from svelte/server (#18648)

### Fixed

- Don't apply scoped CSS class to elements inside <svelte:head> (#18160)
- Don't resurrect outroing elements when an ancestor block is paused and resumed (#18431)
- Preserve whitespace after inline elements when printing (#18685)
- Avoid NaN keyframe values in slide transition (#18430)
- Distinct memoizer on style/class directives (#18466)
- Route $derived teardown errors through invoke_error_boundary (#18486)
- Prevent `selectedcontent` mutation from changing the selected option (#18495)
- Run `onDestroy` callbacks when a server render throws (#18585)
- Make template store subscriptions wait for the promise that assigns the store (#18582)
- Don't turn component instances stored in $state into state proxies (#18646)
- Warn on undeclared shorthand event handlers on svelte:window/document/body (#18480)
- Scope SSR boundary failed snippets to their boundary (#18593)
- Prevent onoutroend from firing twice when compilerOptions.hmr is true (#18655)

### Changed

- Updated docs to include information on easing functions (#16070)
- Optimize simple object destructuring in @const tags (#18390)
- Bump vite from 7.3.2 to 7.3.5 (#18444) (deps-dev)
- Fix typo in read_version JSDoc (#18470)
- Clarify $bindable fallback binding requirement (#18477)
- Clarify when `$effect.pre` runs relative to DOM updates (#18534)
- Replace N-ary times `⨉` with multiplication sign `×` (#18418)
- Fix typo in basic markup doc (#18434)
- Document rune_missing_parentheses compiler error (#18589)
- Added generic type parameter example for $state (#18494)
- O(n²)→O(n) Map lookups for legacy reactive statements (#18602)
- Update mobile FAQ (#18665)

[Сравнение с svelte@5.56.10](https://github.com/sveltejs/svelte/compare/svelte@5.56.10...HEAD)

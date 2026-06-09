# Changelog

## [v16.3.0-canary.46] - 2026-06-09

### Added
  + **Add global config to enable Partial Prefetching (#94448)** — Andrew Clark (f5af284)

### Fixed
  + **fix(dev-overlay): Tidy up issues/insight menu and tab overlay (#94549)** — Aurora Scharff (0a074bd)
  + **Fix: Subtree hints not propagating correctly (#94489)** — Andrew Clark (6611813)

### Removed
  + **Remove dead cacheComponents web streams path (#93944)** — Tim Neutkens (89bd483)
  + **Remove `experimental.useNodeStreams` flag as it's enabled (#93938)** — Tim Neutkens (ec28a4f)
  + **Remove turbopackMemoryLimit it is dead (#94483)** — Luke Sandberg (a51f355)

### Other
  + **Stabilize export const prefetch (#94571)** — Josh Story (adb2913)
  + **[turbopack] Use an arena for `JSValue`s (#94297)** — Sam Poder (409fa64)
  + **[Docs] Remove unstable_instant agent hints; insights validate by default (#94577)** — Jude Gao (7dfd464)
  + **Rename prefetch option `force-runtime` to `allow-runtime` (#94568)** — Josh Story (a953918)
  + **v16.3.0-canary.46** — next-js-bot[bot] (e1affae)
  + **docs: move insight error pages from vercel/front to canary (#94564)** — Aurora Scharff (2cc99c7)
  + **docs: fix onRequestError error type example (#94518)** — Danyal Ahmed (5c9bc5c)
  + **enable eviction by default (#94452)** — Luke Sandberg (7041635)
  + **docs: clarify use cache persistence across deploys (#93554)** — Joseph (9cde916)
  + **[turbopack] Remove WebAssembly helpers from the default runtime (#94373)** — Sam Poder (83eea78)
  + **Reduce new test concurrency to five (#94552)** — Tim Neutkens (c082ffe)
  + **[ci] Disable on-call notification if manual deploy e2e tests failed (#94554)** — Sebastian "Sebbie" Silbermann (00db625)
  + **docs: add updateTag example to cacheTag page (#94508)** — Aurora Scharff (5e14410)
  + **docs: clarify next-env.d.ts regeneration (#94232)** — SJvaca30 (bd9f0eb)
  + **v16.3.0-canary.45** — next-js-bot[bot] (0dc1884)
  + **Turbopack: content hash polyfill sourcemap file (#94548)** — Niklas Mischkulnig (ff86557)
  + **[cna] Use `allowBuilds` instead of `ignoredBuiltDependencies` when using PNPM 11+ (#94544)** — Sebastian "Sebbie" Silbermann (0bded2d)
  + **Turbopack: refactor into `get_next_client_transforms_rules` (#94487)** — Niklas Mischkulnig (f5718d2)
  + **Partial Prefetching: Default to App Shell only (#94510)** — Andrew Clark (16b44a8)
  + **[turbopack] standardize chunk entry names for webpack and postcss loaders (#94256)** — Luke Sandberg (70149d7)
  + **v16.3.0-canary.44** — next-js-bot[bot] (0cc8234)
  + **[turbopack] Enable Effects to be evicted (#94173)** — Luke Sandberg (804b9a0)
  + **enable eviction on canary (#94451)** — Luke Sandberg (0d0dbb6)
  + **Specialize client hook prerender abort reasons (#94494)** — Josh Story (2df0562)


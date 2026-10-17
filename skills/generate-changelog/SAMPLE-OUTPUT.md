<!-- Provenance: real run over chalk/chalk, range v5.0.0..HEAD -->

## [6.0.0] - 2026-10-17

### Added
- Add extended underline styles and underline colors (#689) (4c304dd)
- Update `CIRCLECI` environments to return level 3 color support (f838120)
- Add FAQ to readme (4a10354)
- Add `sideEffects` field to package.json (5aafc0a)
- Add `main` field to package.json for backwards compatibiltiy (85f7e96)

### Fixed
- Fix inconsistent coercion of two arguments (9c93a04)
- Treat a numeric `FORCE_COLOR` as an exact level (#688) (e912931)
- Downsample `ansi256()` and `bgAnsi256()` to 16 colors at level 1 (#687) (ff549c5)
- Fix typos (#664) (aa06bb5)
- Fix `navigator` not defined `ReferenceError` (#642) (4ebb62d)
- Fix CI (df0e69d)
- Fix exported styles names (#569) (a34bcf6)

### Changed
- 6.0.1 (47fc05a)
- Meta tweaks (8960ada)
- 6.0.0 (661317e)
- Improve performance (5729845)
- Require Node.js 22 (8a94e0e)
- Optimize 2-argument calls (#670) (fa5cff2)
- Tweaks (678e550)
- 5.6.2 (5155778)
- 5.6.0 (5c91505)
- Make WezTerm terminal use true color (a8f5bf7)
- 5.5.0 (67db246)
- Make Ghostty terminal use true color (#653) (79ee2d3)
- 5.4.1 (5dbc1e2)
- Readme tweak (fc809b6)
- 5.4.0 (83acfcf)
- Meta tweaks (77126fb)
- Update dependents number in readme (#629) (795273f)
- Tweak example (#623) (386909e)
- Meta tweaks (f399cd0)
- 5.3.0 (72c742d)
- Update `supports-color` to 9.4.0 (#603) (29b8569)
- 5.2.0 (a370f46)
- Update `supports-color` dependency (#579) (7443e9f)
- Minor tweaks (a027e3c)
- Update Replit badge (#576) (79c56df)
- Update link to Truecolor in the readme (#573) (c3d14f9)
- 5.1.2 (158bf44)
- 5.1.1 (1b4cd21)
- Export styles from `ansi-styles` (#567) (6e0df05)
- 5.1.0 (92c55db)
- Expose style names (#566) (d7d7571)
- Meta tweaks (96f44c9)
- Use template literal types for simple color name transformations in the TypeScript types (#564) (c231162)
- Update screenshot (ba5c385)
- Update Replit badge (#551) (503b9d3)
- Improve browser detection (#542) (b17d862)
- Replace deprecated `String#substr()` (#541) (d28690e)
- 5.0.1 (bccde97)

### Removed
- Remove .replit file (#622) (2db3c77)
- Remove repl.it badge (f7b29ae)


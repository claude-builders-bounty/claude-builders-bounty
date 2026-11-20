# Changelog

<!-- generated-by: changelog.sh — regenerate with `bash generate-changelog/changelog.sh`; do not edit the sections below by hand -->

## [Unreleased] (2026-11-20)

_Commits since `8.8.5` (51)_:

### Added

- test: add webcontainers smoke check (#1545) (4e1ea91)
- test: add electron smoke tests (#1544) (33ef7e0)
- Clarify shell requirement and add MAML reference (#1500) (65fc542)
- docs: add npm OIDC example (#1452) (a20f68e)
- Add fire emoji to crow.watch link in README (98531fc)
- feat: introduce `ProcessPromise.cwd` getter (#1414) (f61cbb8)
- feat: provide clear error when cwd directory does not exist (#1407) (4954862)
- Add useful links (4d7bf57)
- feat: introduce `MAML` API (#1362) (73a96e1)

### Fixed

- docs: fix webpod ssh integration example (00a2c48)
- fix(cli): skip protocol imports in `--install` (#1464) (b6bc975)
- fix: update @webpod/ps to v1.2.1 to fix BuzyBox issues (#1455) (7fe54a9)
- fix: add `+` and `%` to `quote` whitelist (#1424) (2bbcaa5)
- fix(core): add comma to safe characters to prevent unnecessary `$'...'` quoting (#1412) (c91c43b)
- fix: enable `.sync` shortcut for `$` presets (#1423) (7a0f133)
- fix: handle all ECMAScript line terminators in `transformMarkdown` (#1416) (cd7f23d)
- fix: handle fence indents in md processor (#1419) (3dd9503)
- refactor(cli): improve error handling for remote script fetch (#1408) (11f1c8e)
- fix(cli): improve internal `isMain` compat with Deno (#1410) (af23fab)
- fix(cli): prevent double extension in temp file for stdin markdown with --ext .md (#1399) (2f6896e)
- fix(log): fix nodejs12 compatibility (#1380) (446b755)
- chore: update deps, fix tsc@next smoke test config (#1373) (b175afd)

### Changed

- chore: update `@webpod/ps` to v1.3.0 (#1546) (3b04a6a)
- docs: migrate to vitepress v2 (#1543) (62f9176)
- chore(deps): yaml@2.9.1, fs-extra@11.4.1, globby@16.2.4 (#1542) (00822ee)
- Update see also section in README.md (#1533) (1e1cdb4)
- chore(deps): update yaml to v2.9.0 (#1491) (d24bef7)
- chore(deps): update `maml` to version 1.0.1 (6a62a4b)
- chore(deps): which 7.0.0, depseek 0.4.6, fs-extra 11.3.5, globby 16.2.0, yaml 2.8.4 (#1466) (aab8095)
- chore: bump fast-uri in the npm_and_yarn group across 1 directory (#1463) (3d51a8d)
- refactor: replace maml.js with maml (#1445) (707b43a)
- chore: update yaml to v2.8.3 and fs-extra 11.3.4 (#1437) (c5da080)
- Update README.md (084484a)
- Update README.md (ab2c21d)
- Update README with Crow Watch details (#1429) (06de626)
- chore: update c8 to v11 (#1426) (6118002)
- refactor: assert promise cmd chunks for `sync` mode (#1422) (1148286)
- chore: force pin `minimatch@10.2.2` to pass npm audit (#1413) (857c401)
- Refactor Github Action per b/485167538 (1c4becd)
- docs: warning for remote scripts execution (#1405) (97e975c)
- docs(pr): mention commits signature requirement (#1397) (c369580)
- chore: update jsr to 0.14.2 (#1396) (7deeea5)
- chore: upgrade GitHub Actions to latest versions (#1391) (8c7c701)
- chore: upgrade GitHub Actions for Node 24 compatibility (#1390) (0fd1789)
- chore: update zizmor to v1.22.0 (#1387) (f19b651)
- chore: update globby to v16.1.0, up dev deps (#1384) (0142804)
- chore: update deps (#1368) (24d41a1)
- chore: bump js-yaml in the npm_and_yarn group across 1 directory (#1366) (9c6cb9b)
- docs: mention `MAML` in versions comparison (#1363) (327bfaa)
- chore: bump vite 5.4.21 (#1360) (240a399)

### Removed

- chore(build): remove redundant `await` from readFileSync calls (#1379) (ff5effa)


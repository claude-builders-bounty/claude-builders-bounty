# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [v1.21.0] - 2026-10-23

### Added

- **core:** expose request duration on the response (#11214) ([`e5195ec`](https://github.com/axios/axios/commit/e5195ec))
- **auth:** add opt-in UTF-8 Basic auth usernames (#11159) ([`4661a7d`](https://github.com/axios/axios/commit/4661a7d))

### Fixed

- **headers:** bind matcher callbacks to the headers instance (#11216) ([`8d415e6`](https://github.com/axios/axios/commit/8d415e6))
- **xhr:** remove progress event listeners on request completion (#11225) ([`b16dd77`](https://github.com/axios/axios/commit/b16dd77))
- **http2:** stop reusing sessions after GOAWAY (#11210) ([`43968f2`](https://github.com/axios/axios/commit/43968f2))
- **xhr:** avoid main-thread jank from cookie reads (#11166) ([`b0842e8`](https://github.com/axios/axios/commit/b0842e8))
- **http:** apply https.globalAgent TLS options to proxy tunnels (#11178) ([`ac90a5f`](https://github.com/axios/axios/commit/ac90a5f))
- **BREAKING:** **core:** keep literal request headers named after a method (#11156) ([`cf744d2`](https://github.com/axios/axios/commit/cf744d2))
- **AxiosError:** inline the wrapped error stack for cause-unaware tooling (#11142) ([`fe2fbf8`](https://github.com/axios/axios/commit/fe2fbf8))
- **interceptors:** restore numeric-string interceptor IDs (#11139) ([`a07c81a`](https://github.com/axios/axios/commit/a07c81a))
- **http:** decode percent-encoded Base64 data URLs (#11294) ([`2b169bb`](https://github.com/axios/axios/commit/2b169bb))
- normalize parsed protocols to lowercase (#11163) ([`28e9b84`](https://github.com/axios/axios/commit/28e9b84))
- **fromDataURI:** accept case-insensitive base64 tokens (#11138) ([`6576f57`](https://github.com/axios/axios/commit/6576f57))
- **AxiosHeaders:** store a header named __proto__ instead of writing through Object.prototype (#11134) ([`e1a8a57`](https://github.com/axios/axios/commit/e1a8a57))
- **core:** preserve short reconstructed request stacks (#11132) ([`c4303ee`](https://github.com/axios/axios/commit/c4303ee))
- align request handling across runtimes (v1.x) (#11242) ([`2498c23`](https://github.com/axios/axios/commit/2498c23))
- **fetch:** preserve response size errors across runtime wrappers (#11179) ([`56a5f1a`](https://github.com/axios/axios/commit/56a5f1a))
- **types:** expose the response default marker type (#11125) ([`fbe2e82`](https://github.com/axios/axios/commit/fbe2e82))
- **fetch:** apply the default cache mode only where the runtime accepts it (#11194) ([`f8df2e2`](https://github.com/axios/axios/commit/f8df2e2))

### Changed

- **chore(release):** prepare release 1.21.0 (#11346) ([`e6b79d9`](https://github.com/axios/axios/commit/e6b79d9))
- **chore(deps-dev):** bump the development_dependencies group with 4 updates (#11342) ([`fceeb10`](https://github.com/axios/axios/commit/fceeb10))
- **docs:** refresh sponsor data (#11341) ([`7d15df3`](https://github.com/axios/axios/commit/7d15df3))
- **docs:** correct interceptor options and request lifecycle guide (#11335) ([`8d8e844`](https://github.com/axios/axios/commit/8d8e844))
- **test(no-proxy):** cover the request-hostname path with a long dotted host (#11235) ([`326843a`](https://github.com/axios/axios/commit/326843a))
- **chore(deps):** bump the github-actions group with 3 updates (#11323) ([`790b2ca`](https://github.com/axios/axios/commit/790b2ca))
- **chore(deps-dev):** bump the development_dependencies group with 4 updates (#11322) ([`e58cf0e`](https://github.com/axios/axios/commit/e58cf0e))
- **chore(deps):** bump follow-redirects from 1.16.0 to 1.16.1 in the production_dependencies group (#11321) ([`37041f5`](https://github.com/axios/axios/commit/37041f5))
- **chore(deps-dev):** bump source-map-js from 1.2.1 to 1.2.2 in /tests/smoke/esm (#11313) ([`82b5643`](https://github.com/axios/axios/commit/82b5643))
- **perf(core):** reduce request configuration merge overhead (#11208) ([`2a9489d`](https://github.com/axios/axios/commit/2a9489d))
- **docs(readme):** update CDN examples to current axios version (#11149) ([`f694ecd`](https://github.com/axios/axios/commit/f694ecd))
- **chore(deps-dev):** bump proxy-addr from 2.0.7 to 2.0.8 (#11306) ([`1a94bdb`](https://github.com/axios/axios/commit/1a94bdb))
- **chore(deps-dev):** bump source-map-js from 1.2.1 to 1.2.2 (#11305) ([`b6bb550`](https://github.com/axios/axios/commit/b6bb550))
- **chore(deps):** bump @vue/server-renderer and vue in /docs (#11304) ([`b4d7feb`](https://github.com/axios/axios/commit/b4d7feb))
- **chore(deps-dev):** bump brace-expansion from 2.1.4 to 2.1.7 in /tests/smoke/cjs (#11303) ([`58a9cf6`](https://github.com/axios/axios/commit/58a9cf6))
- **chore(deps-dev):** bump source-map-js from 1.2.1 to 1.2.2 in /tests/module/esm (#11302) ([`b918341`](https://github.com/axios/axios/commit/b918341))
- **chore(deps-dev):** bump lint-staged from 17.5.1 to 17.6.0 in the development_dependencies group (#11298) ([`a0ed1a2`](https://github.com/axios/axios/commit/a0ed1a2))
- **docs:** clarify that `npm test` requires playwright browsers (#11284) ([`057930b`](https://github.com/axios/axios/commit/057930b))
- **chore(deps-dev):** bump the development_dependencies group across 1 directory with 6 updates (#11271) ([`aab2d17`](https://github.com/axios/axios/commit/aab2d17))
- **chore(deps-dev):** bump brace-expansion from 1.1.12 to 1.1.21 in /tests/module/cjs (#11270) ([`b6e62b1`](https://github.com/axios/axios/commit/b6e62b1))
- **chore(deps-dev):** bump brace-expansion from 5.0.7 to 5.0.12 (#11269) ([`9799ef5`](https://github.com/axios/axios/commit/9799ef5))
- **chore(deps):** bump axios from 1.18.1 to 1.20.0 in /docs (#11268) ([`b328ece`](https://github.com/axios/axios/commit/b328ece))
- **docs:** require prerelease notes and PR validation (#11223) ([`3fa3095`](https://github.com/axios/axios/commit/3fa3095))
- **chore:** standardize pull request labels (#11273) ([`79286c6`](https://github.com/axios/axios/commit/79286c6))
- **docs:** add Code for Japan and Sweepico sponsors (#11252) ([`2426e03`](https://github.com/axios/axios/commit/2426e03))
- **docs:** promote Axios v0 security updates (#11249) ([`961241f`](https://github.com/axios/axios/commit/961241f))
- **chore(deps):** bump zizmorcore/zizmor-action from 0.6.3 to 0.6.4 in the github-actions group (#11245) ([`5fc40e1`](https://github.com/axios/axios/commit/5fc40e1))
- **chore(deps-dev):** bump the development_dependencies group with 3 updates (#11244) ([`24278bd`](https://github.com/axios/axios/commit/24278bd))
- **chore(deps-dev):** bump the development_dependencies group with 4 updates (#11234) ([`ba0f3a0`](https://github.com/axios/axios/commit/ba0f3a0))
- **chore(deps):** bump nanoid from 3.3.17 to 3.3.19 in /docs (#11230) ([`ed95c08`](https://github.com/axios/axios/commit/ed95c08))
- **docs:** fix interceptor test links (#11228) ([`dfa30a7`](https://github.com/axios/axios/commit/dfa30a7))
- **docs:** add HeroDevs as a permanent gold sponsor (#11222) ([`18e7dfe`](https://github.com/axios/axios/commit/18e7dfe))
- **chore(deps-dev):** bump js-yaml from 4.3.1 to 4.3.2 (#11221) ([`1226e6c`](https://github.com/axios/axios/commit/1226e6c))
- **chore(deps):** bump @vitest/mocker and vitest in /tests/smoke/esm (#11220) ([`9ecb985`](https://github.com/axios/axios/commit/9ecb985))
- **chore(deps-dev):** bump js-yaml from 4.1.0 to 4.3.2 in /tests/smoke/cjs (#11218) ([`d1f060d`](https://github.com/axios/axios/commit/d1f060d))
- **chore(deps-dev):** bump the development_dependencies group with 3 updates (#11212) ([`aaf20ba`](https://github.com/axios/axios/commit/aaf20ba))
- **chore(deps):** bump zizmorcore/zizmor-action from 0.6.2 to 0.6.3 in the github-actions group (#11213) ([`6598b71`](https://github.com/axios/axios/commit/6598b71))
- **chore(deps-dev):** bump fast-uri from 3.1.5 to 3.1.7 (#11195) ([`b8d67bb`](https://github.com/axios/axios/commit/b8d67bb))
- **chore(deps-dev):** bump browserslist from 4.28.4 to 4.28.8 (#11189) ([`81df7a5`](https://github.com/axios/axios/commit/81df7a5))
- **chore(deps-dev):** bump the development_dependencies group with 5 updates (#11188) ([`ba1d1f6`](https://github.com/axios/axios/commit/ba1d1f6))
- **chore(deps-dev):** bump the development_dependencies group across 1 directory with 4 updates (#11169) ([`fede1d1`](https://github.com/axios/axios/commit/fede1d1))

### Removed

- **docs:** remove cancelled sponsors from README (#11369) ([`aa54a5e`](https://github.com/axios/axios/commit/aa54a5e))
- **refactor(helpers):** remove Internet Explorer detection from isURLSameOrigin (#11174) ([`f796eb0`](https://github.com/axios/axios/commit/f796eb0))
- **chore(deps):** remove unused chai from CJS module tests (#11272) ([`581cd01`](https://github.com/axios/axios/commit/581cd01))
- **chore(deps):** remove unused root chalk dependency (#11267) ([`bc0f5c9`](https://github.com/axios/axios/commit/bc0f5c9))
- **chore(docs):** remove unused dayjs dependency (#11266) ([`8046ddc`](https://github.com/axios/axios/commit/8046ddc))
- **chore:** remove CLAUDE.md in favor of AGENTS.md (#11238) ([`572142c`](https://github.com/axios/axios/commit/572142c))


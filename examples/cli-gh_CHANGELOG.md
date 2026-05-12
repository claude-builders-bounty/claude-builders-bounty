# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Generated from commits after tag `v2.92.0`.

## [Unreleased]

### Fixed
- hint to run copilot directly when exec fails ([`601dd346`](https://github.com/cli/cli/commit/601dd346b00b357a0541239fb80b34c3795e7c33))
- provide full path to copilot binary on exec error ([`ae7bd54d`](https://github.com/cli/cli/commit/ae7bd54d431cd914b20efab191c6ab357fe24d6a))
- update test assertion to match updated error message ([`24c7b25a`](https://github.com/cli/cli/commit/24c7b25afdb44a12ea823029c3fd7a3092a8be73))

### Changed
- Print `gh auth refresh` for 401 returns ([`a656271f`](https://github.com/cli/cli/commit/a656271f26a591c958f561874ddced4aace18bed))
- Apply patch from code review feedback. ([`c139b17e`](https://github.com/cli/cli/commit/c139b17e9fe007126d9e44d1bd8bab7bac2943f5))
- bump goreleaser/goreleaser-action from 7.0.0 to 7.2.1 ([`ed31e2f6`](https://github.com/cli/cli/commit/ed31e2f6e8b8079115409aec11c7960bf2360cc4))
- Merge pull request #13297 from cli/dependabot/github_actions/goreleaser/goreleaser-action-7.2.1 ([`bd4a06aa`](https://github.com/cli/cli/commit/bd4a06aab7336d3a1113525f0b8088429bdee0e0))
- Add missing //go:build integration tag to verify_integration_test.go ([`20e4d251`](https://github.com/cli/cli/commit/20e4d25147ea90d629d689a01675eac551fc6362))
- Fix flaky Password test by increasing echo mode setup timeout ([`6d6ea5f3`](https://github.com/cli/cli/commit/6d6ea5f3719ca29802005d877b2beaa06beca7df))
- Merge pull request #13303 from pdostal/fix/add-integration-build-tag ([`fae293f8`](https://github.com/cli/cli/commit/fae293f8e84f5db61257315fd29c91e25c6c9eaf))
- Merge pull request #13304 from pdostal/fix/accessible-prompter-password-test-timeout ([`d762f9e2`](https://github.com/cli/cli/commit/d762f9e23296a856fab57241675fa5709ee13da4))
- Enable extended PR screening for external PRs ([`8b89c8b2`](https://github.com/cli/cli/commit/8b89c8b2b2eb9920f944bf3091fda5724ddee717))
- Merge pull request #13312 from cli/enable-pr-screening ([`611b01f6`](https://github.com/cli/cli/commit/611b01f6c88c76671131ffe11cb9bec8502721b5))
- Switch from actions/attest-build-provenance to actions/attest ([`4ed70026`](https://github.com/cli/cli/commit/4ed70026815d71b97b54d2ceeb038e992a34fd55))
- Grammar fixes ([`d8b8655f`](https://github.com/cli/cli/commit/d8b8655f2199bbda719d56a38943d69031095e3a))
- Remove numberFieldOnly API shortcut ([`8ff70e6e`](https://github.com/cli/cli/commit/8ff70e6e7ad6b2df3fd2a6988ed287189dd60ce2))
- bump github.com/klauspost/compress from 1.18.5 to 1.18.6 ([`6dc432ec`](https://github.com/cli/cli/commit/6dc432ec479a00b7fb272327d0e6fbb9350a5519))
- Merge pull request #13327 from cli/wm/fix-pr-view-number-only-optimization ([`50d6008f`](https://github.com/cli/cli/commit/50d6008f4dcb1597acde187627898a47e2b494cf))
- Merge pull request #13068 from 333fred/print-refresh-for-401s ([`7c439196`](https://github.com/cli/cli/commit/7c439196c1fc4d645d091e83029370cef845587c))
- Merge pull request #13326 from scop/style/grammar ([`3c162a78`](https://github.com/cli/cli/commit/3c162a78efc4cf48f6582f261223166af2558a64))
- Bump copilot telemetry sampling to 100% ([`1caa3b74`](https://github.com/cli/cli/commit/1caa3b7475611186a617071106dd415e996b25f1))
- Record accessibility state in telemetry ([`acf2f730`](https://github.com/cli/cli/commit/acf2f730c19dd0bc904969e58a133776698caaf0))
- Merge pull request #13362 from cli/wm-copilot-sampling-100 ([`6176c3ee`](https://github.com/cli/cli/commit/6176c3eee4b70d0ccf3c6a1503035d049ca4e81b))
- Merge pull request #13363 from cli/wm-accessible-telemetry ([`2bc88628`](https://github.com/cli/cli/commit/2bc88628dc86a4bc0dfa499467218f9229365e89))
- Merge pull request #13328 from cli/dependabot/go_modules/github.com/klauspost/compress-1.18.6 ([`9b457e8a`](https://github.com/cli/cli/commit/9b457e8aa2b3785859be4e659c5e3153e21ff15e))
- Poll TTY echo mode instead of sleeping in password tests ([`c48bc1a7`](https://github.com/cli/cli/commit/c48bc1a7d1f4adc9dca524ef99435291b35c24b5))
- Address review feedback on echo mode polling ([`9c4184de`](https://github.com/cli/cli/commit/9c4184de6f8c208a11e4329b90fa9844efd728e9))
- Add explicit build tags to platform-specific echo test files ([`a44721d2`](https://github.com/cli/cli/commit/a44721d233be9a2f6f0b5ee5c4f71274acb8d296))
- Merge pull request #13305 from pdostal/fix/poll-tty-echo-mode-in-password-tests ([`b698aa74`](https://github.com/cli/cli/commit/b698aa7462b87a7fed672744578b2e43e825b829))
- Merge pull request #13325 from scop/chore/actions-attest ([`2297f1f2`](https://github.com/cli/cli/commit/2297f1f2ebc3c81b91120c6efa9257573d4d9862))
- Fix skills acceptance tests ([`f47e459c`](https://github.com/cli/cli/commit/f47e459cf556aa492172491fbfb105af0b18e1b3))
- Merge pull request #13365 from cli/wm-fix-skills-acceptance-tests ([`b77d79c4`](https://github.com/cli/cli/commit/b77d79c4e1d76df1521da93e9a4f6144ede7e1c9))
- Bump Go toolchain to 1.26.3 ([`cdda57e3`](https://github.com/cli/cli/commit/cdda57e3601d2ce94ebae101d0dfa4983479ee6d))
- Merge pull request #13367 from cli/copilot/bump-go-to-1-26-3 ([`7cf93e72`](https://github.com/cli/cli/commit/7cf93e72f21dfe70d2f631da701775b142fae5e7))
- Fix triage-pull-requests skipping PRs that open as draft ([`8fb4f335`](https://github.com/cli/cli/commit/8fb4f3354cb61f30d204eb0673c20d0824e1cef8))
- Merge pull request #13383 from cli/kw/triage-fix-ready-for-review ([`9b505c3f`](https://github.com/cli/cli/commit/9b505c3fb8c3e52100575adbad2da7c4714684d8))
- Merge pull request #13393 from cli/babakks/improve-gh-copilot-error ([`fe996d33`](https://github.com/cli/cli/commit/fe996d33ac852eafdb2769fcba063860be1b4e6a))


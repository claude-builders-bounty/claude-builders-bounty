# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2026-03-29]

### 🚀 Added

- add AI code review bot for bounty PR submissions
- add bounty tracker — notifies Telegram when bounty PRs merge
- add inline action buttons to AI review Telegram notifications
- add PR template requiring Solana wallet for bounty payout
- auto-detect missing wallet in bounty PRs
- add $FNDRY token contract address + Buy on Bags link to README
- bounty tier issue templates (T1/T2/T3)
- workflow_dispatch trigger for manual PR reviews + fix PR body handling
- Claim Guard: auto-reply on T1 bounties when people try to claim FCFS bounties
- add contributor profiles API (#41) [#41](https://github.com/davidweb3-ctrl/solfoundry/pull/41)
- auto-request changes on failing PRs, simplify Telegram buttons
- add leaderboard API with ranking, filters, pagination, and caching (#65) [#65](https://github.com/davidweb3-ctrl/solfoundry/pull/65)
- tier-aware review calibration — risk-based scoring and weighted verdicts
- show Solana wallet + Solscan verify link in Telegram PR notifications
- Landing page redesign with interactive animations (#68) [#68](https://github.com/davidweb3-ctrl/solfoundry/pull/68)
- recalibrate review system with integration scoring and wider score range
- add star reward watcher — auto-notifies Telegram on wallet claims
- enforce T1-before-T2 reputation gate in claim-guard
- CONTRIBUTING.md with tier rules, wallet requirements, and review pipeline docs
- Contributing Guide link to README header and Contributing section
- submission timestamp to PR review Telegram notifications
- wallet warning (24h auto-close), duplicate detection, clearer PR submission docs
- tier eligibility check to PR review + fix claim-guard bug
- duplicate submission check — one PR per person per bounty
- Add Contributor Profile Page component (#91) [#91](https://github.com/davidweb3-ctrl/solfoundry/pull/91)
- Implement GitHub Webhook Receiver (Issue #12) (#73) [#12](https://github.com/davidweb3-ctrl/solfoundry/pull/12)
- Implement Notification System (#71) [#71](https://github.com/davidweb3-ctrl/solfoundry/pull/71)
- Implement Bounty Search & Filter Engine (#56) [#56](https://github.com/davidweb3-ctrl/solfoundry/pull/56)
- implement Site Navigation & Layout Shell component (Issue #18) (#107) [#18](https://github.com/davidweb3-ctrl/solfoundry/pull/18)
- Add CI/CD pipeline with GitHub Actions
- REST API — Bounty CRUD Endpoints (#114) [#114](https://github.com/davidweb3-ctrl/solfoundry/pull/114)
- Auth System with OAuth and Wallet (Issue #11) (#121) [#11](https://github.com/davidweb3-ctrl/solfoundry/pull/11)
- Implement Bounty Detail Page (Issue #21) (#118) [#21](https://github.com/davidweb3-ctrl/solfoundry/pull/21)
- Mobile responsive improvements for ContributorProfile (#117) [#117](https://github.com/davidweb3-ctrl/solfoundry/pull/117)
- Payout History & Treasury Stats API (#127) [#127](https://github.com/davidweb3-ctrl/solfoundry/pull/127)
- Tokenomics Page (#137) [#137](https://github.com/davidweb3-ctrl/solfoundry/pull/137)
- Bounty Board UI — List & Filter Open Bounties (#133) [#133](https://github.com/davidweb3-ctrl/solfoundry/pull/133)
- implement PR Status Tracker component (Issue #23) (#134) [#23](https://github.com/davidweb3-ctrl/solfoundry/pull/23)
- Contributor Leaderboard Page (#131) [#131](https://github.com/davidweb3-ctrl/solfoundry/pull/131)
- agent marketplace with hire flow and comparison (Closes #25) (#148) [#25](https://github.com/davidweb3-ctrl/solfoundry/pull/25)
- Implement Bounty Creation Wizard (Issue #24) (#140) [#24](https://github.com/davidweb3-ctrl/solfoundry/pull/24)
- real-time WebSocket server with auth, heartbeat, and Redis pub/sub (Closes #17) (#153) [#17](https://github.com/davidweb3-ctrl/solfoundry/pull/17)
- Bounty Claiming System (Issue #16) (#145) [#16](https://github.com/davidweb3-ctrl/solfoundry/pull/16)
- wire up full site — routing, layout, Tailwind, API integration
- Live GitHub Issues sync for bounty board + leaderboard
- Client-side GitHub API fetch for bounties + leaderboard
- Agent Profile Page (Closes #204) (#223) [#204](https://github.com/davidweb3-ctrl/solfoundry/pull/204)
- implement $FNDRY wallet staking flow for bounty creation (#211) [#211](https://github.com/davidweb3-ctrl/solfoundry/pull/211)
- Complete implementation of API Rate Limiting & Security Middleware (#180) [#180](https://github.com/davidweb3-ctrl/solfoundry/pull/180)
- Agent Registration API (Closes #203) (#220) [#203](https://github.com/davidweb3-ctrl/solfoundry/pull/203)
- Implement Creator dashboard (#222) [#222](https://github.com/davidweb3-ctrl/solfoundry/pull/222)
- Complete Email Notification Service (#182) [#182](https://github.com/davidweb3-ctrl/solfoundry/pull/182)
- Bounty Timeline Component (Closes #206) (#225) [#206](https://github.com/davidweb3-ctrl/solfoundry/pull/206)
- max 5 submission attempts per user per bounty
- centralize error handling (#235) [#235](https://github.com/davidweb3-ctrl/solfoundry/pull/235)
- polish api auto-generated docs (#249) [#249](https://github.com/davidweb3-ctrl/solfoundry/pull/249)
- Contributor Reputation System (#250) [#250](https://github.com/davidweb3-ctrl/solfoundry/pull/250)
- implement contributor onboarding (#254) [#254](https://github.com/davidweb3-ctrl/solfoundry/pull/254)
- Add Loading Skeletons & Empty States components (#274) [#274](https://github.com/davidweb3-ctrl/solfoundry/pull/274)
- CI/CD Pipeline + Docker + Staging Deploy (#256) [#256](https://github.com/davidweb3-ctrl/solfoundry/pull/256)
- add WalletAddress component with copy-to-clipboard (#294) [#294](https://github.com/davidweb3-ctrl/solfoundry/pull/294)
- real-time WebSocket event server with typed events and polling fallback (Closes #166) (#293) [#166](https://github.com/davidweb3-ctrl/solfoundry/pull/166)
- automated payout pipeline with queue, locks, and transfer execution (Closes #167) [#167](https://github.com/davidweb3-ctrl/solfoundry/pull/167)
- Add Dark/Light Theme Toggle (Closes #259) (#299) [#259](https://github.com/davidweb3-ctrl/solfoundry/pull/259)
- Add TokenPrice component with DexScreener API integration
- automated payout pipeline with SPL transfers, queue, and admin gate (Closes #167) [#167](https://github.com/davidweb3-ctrl/solfoundry/pull/167)
- implement backend health check endpoint with diagnostics (#343) [#343](https://github.com/davidweb3-ctrl/solfoundry/pull/343)
- Add CountdownTimer component (Closes #341) [#341](https://github.com/davidweb3-ctrl/solfoundry/pull/341)
- Add Breadcrumb navigation (Closes #346) [#346](https://github.com/davidweb3-ctrl/solfoundry/pull/346)
- Add TierProgressBar component (Closes #342) (#383) [#342](https://github.com/davidweb3-ctrl/solfoundry/pull/342)
- add legacy fields to health check for bot compatibility and fix uptime calculation
- implement bounty lifecycle management (#353) [#353](https://github.com/davidweb3-ctrl/solfoundry/pull/353)
- PostgreSQL Full Migration — DB-First Reads (Closes #162) (#394) [#162](https://github.com/davidweb3-ctrl/solfoundry/pull/162)
- Add bounty stats API endpoint (Closes #344) (#390) [#344](https://github.com/davidweb3-ctrl/solfoundry/pull/344)
- Add ScrollToTop button component (#413) [#413](https://github.com/davidweb3-ctrl/solfoundry/pull/413)
- review workflow v3.1 — merge-base diff, domain filter, resubmission detection
- migrate contributor & leaderboard services to PostgreSQL (Closes #186) (#416) [#186](https://github.com/davidweb3-ctrl/solfoundry/pull/186)
- implement production grade api rate limiting (#421) [#421](https://github.com/davidweb3-ctrl/solfoundry/pull/421)
- Production security hardening — all 11 requirements (Closes #197) (#443) [#197](https://github.com/davidweb3-ctrl/solfoundry/pull/197)
- connect frontend to real backend API with React Query (Closes #185) (#447) [#185](https://github.com/davidweb3-ctrl/solfoundry/pull/185)
- add custom 404 Not Found page (Closes #338) (#450) [#338](https://github.com/davidweb3-ctrl/solfoundry/pull/338)
- email notification service (#449) [#449](https://github.com/davidweb3-ctrl/solfoundry/pull/449)
- add MarkdownRenderer component with syntax highlighting (Closes #345) (#451) [#345](https://github.com/davidweb3-ctrl/solfoundry/pull/345)
- Add Footer component (Closes #339) (#381) [#339](https://github.com/davidweb3-ctrl/solfoundry/pull/339)
- Dispute Resolution System (Closes #192) (#456) [#192](https://github.com/davidweb3-ctrl/solfoundry/pull/192)
- end-to-end integration testing suite (Closes #196) [#196](https://github.com/davidweb3-ctrl/solfoundry/pull/196)
- End-to-End Integration Testing Suite (Closes #196) (#457) [#196](https://github.com/davidweb3-ctrl/solfoundry/pull/196)
- closed-bounty guard to public shim — block PRs before dispatch
- Phase 3 pre-launch hardening — spam, escrow, tier access, review pipeline
- Add TimeAgo component for relative timestamps (#486) [#486](https://github.com/davidweb3-ctrl/solfoundry/pull/486)
- Apply TimeAgo to ActivityFeed component
- Apply TimeAgo to ContributorProfile
- Add CopyAddress component for bounty #480 [#480](https://github.com/davidweb3-ctrl/solfoundry/pull/480)
- Enhanced Footer component for bounty #478 [#478](https://github.com/davidweb3-ctrl/solfoundry/pull/478)
- Add Tooltip component for bounty #484 [#484](https://github.com/davidweb3-ctrl/solfoundry/pull/484)

### 🐛 Fixed

- add missing datetime import in ai_review.py
- skip duplicate Telegram notification when review triggered from bot
- aggregate_reviews crash when LLM returns non-string issues/suggestions
- spam filter auto-closes PRs with rules comment + fix node_modules false positive
- shell escaping in ai-review CI for PR bodies with special characters
- claim-guard YAML syntax error — move to Python to avoid shell/YAML escaping conflicts
- improve wallet extraction patterns for multi-chain PR bodies
- rebrand landing page to SolFoundry, remove orphaned files
- expand wallet regex to 48 chars — 45-char Solana addresses were rejected
- upgrade claim-guard — delete spam, block bulk claimers, handle all tiers
- exempt content bounties and star reward from claim-guard
- tier gating requires real bounty PRs only
- claim-guard regex + wallet-check triggers re-review
- reward regex handles commas (200,000 was showing as 000)
- add base58 dep — wallet detection was silently failing
- prevent star reward spam from duplicate comments
- auto-delete comments from warned users on T2/T3 bounties
- update claim-guard T2/T3 review score display to match new thresholds
- Tailwind v4 theme config — define custom colors via @theme CSS
- notification system overhaul + bounty board cleanup
- auto-close competing PRs on merge + skip merged PR edits
- implement correct 3-tier bounty system
- Suppress CodeRabbit inline comments and summary
- allow re-reviews on workflow_dispatch by clearing old review comments
- check both PR title and body for Closes #N, handle cross-repo format
- use Python for issue extraction to prevent shell injection from PR body
- add anthropic SDK + missing API keys to review pipeline
- disable cancel-in-progress to unblock PR merges
- paginate PR fetching in claim-guard + fix T3 eligibility rules
- prevent wallet-check from dispatching duplicate reviews
- remove yuzengbaao from leaderboard, fix reputation scoring
- auto-close competing PRs on issue close + check titles
- match 'Issue #N' and 'bounty #N' in PR issue extraction
- raise PR submission limit from 5 to 50 per bounty
- pass Anthropic + DeepSeek API keys to review pipeline
- add anthropic + httpx to review pipeline dependencies
- pass action field in review dispatch payload
- address all review feedback for E2E testing suite (#196) [#196](https://github.com/davidweb3-ctrl/solfoundry/pull/196)
- address all review feedback for E2E testing suite (#196) [#196](https://github.com/davidweb3-ctrl/solfoundry/pull/196)
- restore review shim + fix callback handler crash
- CodeRabbit leaking public comments on PRs
- callback handler: idempotency + merge ordering
- claim-guard bulk check + bounty-tracker concurrency
- leaderboard: PR link extraction, points display, banned list
- Address AI review feedback for TimeAgo component
- Fix failing TimeAgo tests
- Add conditional check for missing createdAt in BountyListView
- Add test for no auto-update on dates older than 7 days
- Address CodeRabbit review feedback (batch 2)

### 🔧 Changed

- refactor: clean up wallet-check action
- tokenomics, roadmap progress, and  distribution details
- README: agentic economy vision, correct LLM models, growing tokenomics
- tier system: T1+T2 open race, T3 claim-based. Add new category labels to issue templates. Update CONTRIBUTING.md and README.
- roadmap to reflect phased bounty structure
- refactor: strict spec compliance for health check, fixed uptime clock, shared redis context, 100% test coverage
- refactor: replace pr-review with thin trigger shim
- T3 threshold references: 7.5 → 7.0 across docs and bot messages

### 📚 Documentation

- s: update README + CONTRIBUTING for 5-model review and tier changes
- s: Add shields.io badges to README for bounty #488 [#488](https://github.com/davidweb3-ctrl/solfoundry/pull/488)

### 🧪 Tests

- mock underlying dependencies for error coverage logic and secure logging

### 🔒 Security

- add .gitignore to prevent secret exposure
- hardening: webhook fail-closed, CORS lockdown, wallet injection fix
- redact wallets in public comments, fix shell injection in workflows


# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased] - 2026-05-28

### Added

- feat(docs): render article content using high-fidelity ReactMarkdown and style premium elements ([768f030](../../commit/768f030))
- feat(routing): integrate automatic isDocsSubdomain route scanner inside App.jsx ([0cecc95](../../commit/0cecc95))
- feat(showcase): create and route 6 missing public showcase pages and link them in landing footer ([1522323](../../commit/1522323))
- feat(docs): make docs portal a standalone page outside of user layout with premium header ([fbf1dbf](../../commit/fbf1dbf))
- feat(docs): add premium documentation portal and fix jsconfig compilation ([b460068](../../commit/b460068))
- feat(auth): add clean self-contained cookie auth endpoints ([c9947d7](../../commit/c9947d7))
- add realtime ticket dashboard updates via Supabase channels ([9978402](../../commit/9978402))
- feat(issue-41): Add automated ticket auto-close cron and notification routing ([a584970](../../commit/a584970))
- add confidence gate for auto-resolve logic ([7971bc8](../../commit/7971bc8))
- replace static thresholds with dynamic system_settings DB fetch ([66111cc](../../commit/66111cc))
- simplify incident management dashboard labels in tickets directory view ([ea04a2d](../../commit/ea04a2d))
- simplify user registry dashboard to clean user-friendly terms and render profile pictures ([837c913](../../commit/837c913))
- render user profile pictures inside admin ticket views and dashboard table ([e8250df](../../commit/e8250df))
- override weak ML predictions with LLM categorization for multilingual support ([954b1aa](../../commit/954b1aa))
- add backend readiness healthcheck ([c88ced5](../../commit/c88ced5))

### Fixed

- fix(auth): add client-side password complexity validation to prevent Supabase error (#253) ([fb6a950](../../commit/fb6a950))
- fix(jsconfig): remove invalid ignoreDeprecations compiler option ([72cf900](../../commit/72cf900))
- fix(media,entities): resolve screenshot and extracted entities display bugs on Ticket Detail page ([8c5462d](../../commit/8c5462d))
- fix(media): resolve image attachment not showing in ticket details ([0bd500d](../../commit/0bd500d))
- graceful degradation for SentenceTransformer offline load (#54) ([1160abb](../../commit/1160abb))
- add current password verification before password update ([7bef2b8](../../commit/7bef2b8))
- clear ticketStore persisted state on logout to prevent cross-user data leakage ([ce422e8](../../commit/ce422e8))
- add GitHub Models bridge for PR checks ([d757398](../../commit/d757398))
- fix(auth): intercept 'Failed to fetch' error and show ad-blocker warning ([f7f7f27](../../commit/f7f7f27))
- handle split SSE chunks in AI stream parsing ([868353a](../../commit/868353a))
- correct profiles join foreign key aliases in analytics and dashboard query ([c351b74](../../commit/c351b74))
- resolve CSAT rating modal flickering and enable dynamic updates ([a8ee74f](../../commit/a8ee74f))
- resolve infinite loading spinner in AdminAnalytics on success ([dfd26f4](../../commit/dfd26f4))
- resolve select dropdown stretching and misalignment in admin settings ([f526b9a](../../commit/f526b9a))
- resolve user name query alias causing 'System' fallbacks ([fc7ec4f](../../commit/fc7ec4f))
- resolve race conditions on analytics/dashboard mounts and simplify loader text ([a015a4a](../../commit/a015a4a))
- resolve user_requests 404 errors and correct CORS headers on user approval email Edge Function ([b54d11b](../../commit/b54d11b))
- update Gemini models to working flash, sync ticket creation with Zustand store, and fix MobileApp ImagePicker crashes ([13c8ec4](../../commit/13c8ec4))
- resolve TDZ ReferenceError and integrate SSE buffering PR ([808be3f](../../commit/808be3f))
- copy .gitattributes and init LFS for Hugging Face deploy ([073d445](../../commit/073d445))
- resolve TDZ error in DuplicateDetection by hoisting resolutionSteps ([16cc4ff](../../commit/16cc4ff))
- refactor AIProcessing stores to top-level react hooks to prevent TDZ initialization errors ([af44167](../../commit/af44167))
- restore missing framer-motion imports and optimize eslint config for JSX recognition ([867bd30](../../commit/867bd30))
- harden readiness healthcheck ([28f6028](../../commit/28f6028))
- handle classifier_v3 fallback gracefully to prevent confidence keyerror ([9390c3e](../../commit/9390c3e))
- use jsonable_encoder to prevent json.dumps crash on numpy types in SSE stream ([c29bbeb](../../commit/c29bbeb))
- resolve github action deployment error and missing favicon ([7c42140](../../commit/7c42140))

### Changed

- chore(gssoc): commit open GSSoC issues remaining triaged scripts ([5ec2591](../../commit/5ec2591))
- chore(gssoc): add GSSoC issues triage and PR merge scripts ([e2d4727](../../commit/e2d4727))
- refactor(dyn): eliminate hardcoded values and configure dynamic variables across UI and config ([64156c2](../../commit/64156c2))
- remove redundant and failing LFS hf_sync.yml workflow ([e723b92](../../commit/e723b92))
- resolve duplicate key in eslint config and clean up unused eslint-disable directives ([02763ef](../../commit/02763ef))
- rename company_settings to system_settings, clean up column names for schema alignment with PR #42 ([143dbdd](../../commit/143dbdd))
- enforce gssoc target branch for pull requests in CONTRIBUTING.md ([e7b4a5d](../../commit/e7b4a5d))
- simplify analytics terms, join profiles database, and optimize live-feed mobile height ([b6f77d4](../../commit/b6f77d4))
- simplify and humanize dashboard and table labels ([5f78398](../../commit/5f78398))
- simplify and humanize system settings labels ([5f5865a](../../commit/5f5865a))
- simplify and humanize all labels in Admin Profile section ([ca6ce60](../../commit/ca6ce60))
- force add ML models to Git LFS ([bbd6f03](../../commit/bbd6f03))
- upload ML models using Git LFS ([948c5c5](../../commit/948c5c5))
- remove unused formatRelativeTime import from RecentTickets component ([a77c695](../../commit/a77c695))
- resolve ESLint warnings and errors by adding necessary ignore comments and improving dependency management across the codebase ([9ecd3d1](../../commit/9ecd3d1))
- Update admin signup placeholders & clean workspace ([b1f664c](../../commit/b1f664c))
- Optimize repository for GSSoC 2026 with badges and guidelines ([a6d430d](../../commit/a6d430d))

### Other

- Privacy: pseudonymize user_id in audit logs ([122fbec](../../commit/122fbec))
- Security hardening: enforce tenant authorization and validation ([80531f2](../../commit/80531f2))
- Fix tenant linkage by persisting company_id on ticket save ([19ae02a](../../commit/19ae02a))
- Fix frontend lint warnings ([3982385](../../commit/3982385))
- Resolve merge conflicts in Frontend files and fix build ([cd58b5e](../../commit/cd58b5e))
- Fix remaining frontend lint issues ([7072e2d](../../commit/7072e2d))
- Fix issue 44 frontend lint and backend contract drift ([bafbdd4](../../commit/bafbdd4))
- clean: remove temporary scratch files, lint reports, and debug scripts from repo ([124d445](../../commit/124d445))
- Fix: saved tickets not added to duplicate detection index (#29) ([a5f2899](../../commit/a5f2899))
- Fix duplicate indexing warning handling and fallback logic ([5e3c61f](../../commit/5e3c61f))
- Fix duplicate detection indexing for saved tickets ([d15f8b1](../../commit/d15f8b1))


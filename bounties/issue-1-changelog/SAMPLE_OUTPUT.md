# Changelog

## [1.0.0] — 2026-03-27

### Added
- feat(bounty-hunter): auto-solve CF Turnstile challenges in guardedFetch (Pi Agent)
- feat(tools): twitter-post.py/js — poster sur @SR_Cryptos via Brave Profile 4 (Fino) sans API Twitter (Pi Agent)
- feat(web-bot-auth): publish JWKS to fino-oss public Gist, update submission doc (Pi Agent)
- feat(bounty-hunter): integrate signedFetch into guardedFetch + patch scan.js direct fetch() calls (Pi Agent)
- feat(identity): Cloudflare Web Bot Auth — Ed25519 signing module + submission doc (Pi Agent)
- feat(bounty-hunter): replace HTTP fetch with Playwright for Superteam CSR pages (Pi Agent)
- feat(bounty-hunter): add watch.js periodic scanner + launchd daemon (Pi Agent)
- feat(bounty-hunter): add Superteam Earn source + real money filter + human blocker detection (Pi Agent)
- feat(routing): add Step 0 problem-type filter (metric-shaped vs software-shaped) + auto-optimize in Domain Skills table (Pi Agent)
- feat(pi-remote): implement voice message handler (Telegram → Groq Whisper → Claude) (Pi Agent)
- feat(evals): add prototype-mvp A/B evals + update run-ab.js — 15/15 passing (Pi Agent)

### Fixed
- fix(watch): 'deadline passed' sur toutes les bounties GitHub/OnlyDust (Pi Agent)
- fix(guard): use cf_clearance cookie flow instead of header for CF Turnstile (Pi Agent)
- fix(bounty-hunter): filter fake token repos (RustChain/RTC) from GitHub scanner (Pi Agent)
- fix(pi-remote): formatForTelegram — remplacer sentinelles par split-escape-join (Pi Agent)
- fix(pi-remote): remap .oga→.ogg for Groq Whisper — Telegram voice format rejected (Pi Agent)
- fix(pi-remote): atomic poll lock with O_EXCL to prevent 7-8 simultaneous pollers (Pi Agent)
- fix(pi-remote): sentinel \x00→\x02/\x03 dans formatForTelegram — null bytes strippés causaient CODE0 visible (Pi Agent)
- fix(pi-remote): accepter /remote-stop, /remote-restart, /remote-reload depuis Telegram (aliases des commandes courtes) (Pi Agent)
- fix(pi-remote): race condition — generation counter prevents stale poll loops stacking on reload (Pi Agent)

### Changed
- chore: init — snapshot initial de l'infrastructure agent (Pi Agent)

### Other
- checkpoint: 20260327-1305 — feat(p8): multicall retry count in scan summary (Pi Agent)
- checkpoint: 20260327-0102 — feat(tools): add sms-reader.js — iPhone SMS gateway via SMSMobileAPI + OTP extraction (Pi Agent)
- checkpoint: 20260326-1810 — feat(captcha): GateSolve x402 integration — captcha-solver.py + captcha-solver.js, API key (100 free solves), wallet verified 3.78 USDC on Base (Pi Agent)
- checkpoint: 20260326-1605 — feat(tools): browser-use bridge — Node.js→Python Playwright automation (Pi Agent)
- checkpoint: 20260324-1800 — feat(tools): add git-checkpoint.sh + AGENTS.md reference (Pi Agent)


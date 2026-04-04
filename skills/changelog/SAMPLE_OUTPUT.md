# Changelog

All notable changes to this project will be documented in this file.

---

## [v1.0.0] — 2026-04-04

### Added
- feat: slowapi rate limiting — app-layer replacement for Caddy rate_limit plugin (#45) (9ce814b)
- feat: Deterministic Replay Viewer (#43) (588f6c7)
- feat: Best-of-N series format — true round-win semantics (#42) (1ca7731)
- feat: ELO ladder — per-wallet ratings, rankings UI, backfill endpoint (#41) (166d839)
- feat: add lag_frames env atom to expression controller context (#40) (c573b68)
- feat: seed-derived mandatory reaction delay 5-15 frames (#39) (234ef98)
- feat: harder difficulty — wider score divergence, fewer ties (#38) (c3d2010)
- feat: finalize seed at acceptChallenge via blockhash to prevent seed-sniping (#36) (97b2cce)
- feat: predicted_x pre-computed env atom for expression controllers (4e60c07)
- feat: wallet signature verification for /session/simulate (0ed7e80)
- feat: expression tree controller + reaction_delay integration (2139332)
- feat: reaction_delay param for /session/simulate (0-30 frames) (967d524)
- feat: on-chain strategy commit-reveal mechanic (c85b8a4)
- feat: /session/simulate + fix AI difficulty (30+ai*30 vs 180+ai*200) (e6156da)
- feat: add /session/simulate with correct Pong.js physics port (da6ba32)
- feat: add /session/simulate endpoint with Python Pong physics (4b065b7)
- feat: standalone pong-test.html for game mechanics iteration (cabe2d7)
- feat: keyboard controls for Pong (arrow keys + A/D) (4196e3e)
- feat: auto-resolve + fix rawTransaction web3.py 6.x compat (b2fe661)
- feat: serve frontend via nginx — VITE_GAME_SERVER_URL baked via build arg (29ed54e)
- feat: sealed message UI + new contract address (ed82f2c)
- feat: sealed message mechanic (Option B+E) — 41/41 tests passing (c683955)
- feat: leaderboard — SQLite match history, /leaderboard endpoint, Leaderboard UI tab (7e26afb)
- feat: replace Tap Duel with Pong (154a861)
- feat: lobby flow — USDC approve + createChallenge + acceptChallenge UI (d3eba32)
- feat: frontend scaffold — React/Vite/Phaser.js Tap Duel game (2146569)
- feat: game server scaffold — FastAPI oracle, Docker, docker-compose (7263a7e)
- add INFRACTIONS.md — ledger initialized with 2026-03-10 entries (4146b12)
- feat: optional whitelist for createChallenge — restrict accepted opponents (652a4b0)
- feat: add NO_DIGGITY.md (immutable) (#1) (f572f3f)
- feat: add game server skeleton (Tap Duel oracle, FastAPI) (e4d6441)
- feat: initial ArcadeDuel contract, tests, deploy script (011893a)

### Fixed
- fix: leaderboard sync — use getChallenge (12 fields), derive winner from scores (#35) (6b1dbd9)
- fix: leaderboard recording for simulate-based matches + /leaderboard/sync backfill (fe841b5)
- fix: oracle gas priority fee 1gwei → 0.001gwei (was draining balance fast) (c20c63a)
- fix: expression controller player speed 300px/s (~5px/frame) (cb30267)
- fix: add audit logging to /session/simulate (wallet + strategy + score) (9bd49d3)
- fix: AI speed formula in simulate_pong (180+ai*200 → 30+ai*30) (7c433a9)
- fix: seeded RNG + remove _sim_pong duplicate (64cc076)
- fix: pong-test.html mouse/keyboard conflict + canvas dimensions match main game (878bf11)
- fix: remove pinned eth-account (conflicts with web3==6.20.0) (389336e)
- fix: wrap wait_for_transaction_receipt in asyncio.to_thread to prevent event loop deadlock (59dd677)
- fix: only record_match in SQLite after confirmed on-chain TX (34afd59)
- fix: pass RPC_URL to game server container (publicnode, not blocked sepolia.base.org) (4246c5e)
- fix: add fallback gas limits to all writeContract calls (775c47e)
- fix: frontend on port 3000 (port 80 occupied on host) (e20dfc6)
- fix: use python3 for healthcheck (no curl in container) (a08125d)
- fix: PORT=8766 to match docker-compose port mapping and health check (c132fa3)
- fix: auto-route to challenge status after creation (1.5s delay to show ID) (6af87f2)
- fix: add session race condition lock + minimum elapsed time check (bb7829b)
- fix: reveal_times stored as relative ms from run start (not absolute epoch) (5cf70a8)
- fix: quick-wins from Opus security review (3e79f7e)
- fix: correct getChallenge ABI tuple to match contract struct (ab2ef83)
- fix: invert score so higher = better (matches resolveChallenge); guard frontend compose (1f2b514)
- fix: whitelist max 50 addrs, duplicate check, test fixes (6093792)
- fix: race condition lock, round completion check, sig hex, EIP-1559 gas, token in POST body (16df993)
- fix: claimTimeout status consistency, cancelChallenge griefing vector (91ea959)
- fix: min wager 0.001 USDC, tie flag in ChallengeResolved event (23eb3b9)

### Changed
- chore: update to v4 contract 0x26C6...532F9 — seriesLength + ELO ABI (10dcddb)
- chore: update CONTRACT_ADDRESS to new deployment (0xD47acC1b...) (#37) (f949cee)
- chore: re-pin requirements to verified working container versions (5fea648)
- chore: update .env.example with current contract + oracle addresses (e964450)
- chore: update game-server ABI for sealed message mechanic (7c44d5f)
- chore: move INFRACTIONS.md and NO_DIGGITY.md to agent-ledger repo (abd5e7a)
- chore: restructure INFRACTIONS.md as running ledger with lessons and merits (ca51940)
- chore: log Alexa infraction #2 (direct push to main) (3cc9200)
- chore: add INFRACTIONS.md — response protocol violation tracker (092108b)

### Removed
- remove INFRACTIONS.md — ledger lives in bouncerpen/agent-ledger (a671a9c)

### Other
- contracts: add SCORE_NET_OFFSET constant + document net score encoding in submitScore NatSpec (#52) (225fbfe)
- game-server: net score (player_score - ai_score) replaces raw score (#51) (16a48a7)
- security: lock CORS to arcadeduel.org (was wildcard *) (3ef48c0)
- ux: reset paddles to center + brief pause between points (#48) (e5eb43a)
- difficulty v2: equal-speed AI + reaction delay + wider canvas + faster ball (#47) (443bd80)
- balance: raise AI speed 65–75 → 200 px/s (#46) (758c883)
- infra: nginx config + setup guide for arcadeduel.org (#44) (7221b87)
- docs: fix stale NatSpec on cancelChallenge (3473462)


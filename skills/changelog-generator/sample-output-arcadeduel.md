# Changelog

## [Unreleased] — 2026-04-04

### Added

- feat: add _predict_after_bounce helper and predicted_ball_x_after_bounce env atom (`2b88684`) — *SecretAgentAlexa*
- pvp: add opponent_predicted_x, round_id, challenge_id env atoms (closes #53) (`228d7b1`) — *SecretAgentAlexa*
- contracts: add SCORE_NET_OFFSET constant + document net score encoding in submitScore NatSpec (#52) (`225fbfe`) — *bouncerpen*
- ux: reset paddles to center + brief pause between points (#48) (`e5eb43a`) — *bouncerpen*
- feat: slowapi rate limiting — app-layer replacement for Caddy rate_limit plugin (#45) (`9ce814b`) — *bouncerpen*
- feat: Deterministic Replay Viewer (#43) (`588f6c7`) — *bouncerpen*
- feat: Best-of-N series format — true round-win semantics (#42) (`1ca7731`) — *bouncerpen*
- feat: ELO ladder — per-wallet ratings, rankings UI, backfill endpoint (#41) (`166d839`) — *bouncerpen*
- feat: add lag_frames env atom to expression controller context (#40) (`c573b68`) — *bouncerpen*
- feat: seed-derived mandatory reaction delay 5-15 frames (#39) (`234ef98`) — *Alexa*
- feat: harder difficulty — wider score divergence, fewer ties (#38) (`c3d2010`) — *bouncerpen*
- chore: update CONTRACT_ADDRESS to new deployment (0xD47acC1b...) (#37) (`f949cee`) — *Alexa*
- feat: finalize seed at acceptChallenge via blockhash to prevent seed-sniping (#36) (`97b2cce`) — *bouncerpen*
- feat: predicted_x pre-computed env atom for expression controllers (`4e60c07`) — *bouncerpen*
- feat: wallet signature verification for /session/simulate (`0ed7e80`) — *AlexaFleisherTheHo*
- feat: expression tree controller + reaction_delay integration (`2139332`) — *AlexaFleisherTheHo*
- feat: reaction_delay param for /session/simulate (0-30 frames) (`967d524`) — *AlexaFleisherTheHo*
- feat: on-chain strategy commit-reveal mechanic (`c85b8a4`) — *AlexaFleisherTheHo*
- feat: /session/simulate + fix AI difficulty (30+ai*30 vs 180+ai*200) (`e6156da`) — *AlexaFleisherTheHo*
- feat: add /session/simulate with correct Pong.js physics port (`da6ba32`) — *Alexa*
- feat: add /session/simulate endpoint with Python Pong physics (`4b065b7`) — *Alexa*
- feat: standalone pong-test.html for game mechanics iteration (`cabe2d7`) — *AlexaFleisherTheHo*
- feat: keyboard controls for Pong (arrow keys + A/D) (`4196e3e`) — *AlexaFleisherTheHo*
- feat: auto-resolve + fix rawTransaction web3.py 6.x compat (`b2fe661`) — *AlexaFleisherTheHo*
- feat: serve frontend via nginx — VITE_GAME_SERVER_URL baked via build arg (`29ed54e`) — *AlexaFleisherTheHo*
- chore: update .env.example with current contract + oracle addresses (`e964450`) — *AlexaFleisherTheHo*
- feat: sealed message UI + new contract address (`ed82f2c`) — *AlexaFleisherTheHo*
- feat: sealed message mechanic (Option B+E) — 41/41 tests passing (`c683955`) — *bouncerpen*
- feat: leaderboard — SQLite match history, /leaderboard endpoint, Leaderboard UI tab (`7e26afb`) — *AlexaFleisherTheHo*
- feat: replace Tap Duel with Pong (`154a861`) — *AlexaFleisherTheHo*
- feat: lobby flow — USDC approve + createChallenge + acceptChallenge UI (`d3eba32`) — *AlexaFleisherTheHo*
- feat: frontend scaffold — React/Vite/Phaser.js Tap Duel game (`2146569`) — *AlexaFleisherTheHo*
- feat: game server scaffold — FastAPI oracle, Docker, docker-compose (`7263a7e`) — *AlexaFleisherTheHo*
- add INFRACTIONS.md — ledger initialized with 2026-03-10 entries (`4146b12`) — *Ubuntu*
- feat: optional whitelist for createChallenge — restrict accepted opponents (`652a4b0`) — *Ubuntu*
- chore: add INFRACTIONS.md — response protocol violation tracker (`092108b`) — *AlexaFleisherTheHo*
- feat: add NO_DIGGITY.md (immutable) (#1) (`f572f3f`) — *bouncerpen*
- feat: add game server skeleton (Tap Duel oracle, FastAPI) (`e4d6441`) — *Alexa*
- feat: initial ArcadeDuel contract, tests, deploy script (`011893a`) — *Ubuntu*

### Fixed

- fix: P2 predicted_x target y was W-PLAYER_Y (280) instead of AI_CY (30) (`052e9b5`) — *SecretAgentAlexa*
- fix: pvp P2 spin transfer symmetric with P1 (offset*40, speed increment, normalize) (`d1deac7`) — *SecretAgentAlexa*
- fix: hoist _mulberry32 to module level for simulate_pong_pvp; fix indent (`57e4e6a`) — *SecretAgentAlexa*
- fix: pvp series mode — submit both gamesWon before resolve_onchain (`67686f7`) — *SecretAgentAlexa*
- fix: leaderboard sync — use getChallenge (12 fields), derive winner from scores (#35) (`6b1dbd9`) — *Alexa*
- fix: leaderboard recording for simulate-based matches + /leaderboard/sync backfill (`fe841b5`) — *bouncerpen*
- fix: oracle gas priority fee 1gwei → 0.001gwei (was draining balance fast) (`c20c63a`) — *AlexaFleisherTheHo*
- fix: expression controller player speed 300px/s (~5px/frame) (`cb30267`) — *AlexaFleisherTheHo*
- fix: add audit logging to /session/simulate (wallet + strategy + score) (`9bd49d3`) — *AlexaFleisherTheHo*
- fix: AI speed formula in simulate_pong (180+ai*200 → 30+ai*30) (`7c433a9`) — *AlexaFleisherTheHo*
- fix: seeded RNG + remove _sim_pong duplicate (`64cc076`) — *AlexaFleisherTheHo*
- fix: pong-test.html mouse/keyboard conflict + canvas dimensions match main game (`878bf11`) — *AlexaFleisherTheHo*
- fix: remove pinned eth-account (conflicts with web3==6.20.0) (`389336e`) — *AlexaFleisherTheHo*
- fix: wrap wait_for_transaction_receipt in asyncio.to_thread to prevent event loop deadlock (`59dd677`) — *AlexaFleisherTheHo*
- fix: only record_match in SQLite after confirmed on-chain TX (`34afd59`) — *AlexaFleisherTheHo*
- fix: pass RPC_URL to game server container (publicnode, not blocked sepolia.base.org) (`4246c5e`) — *AlexaFleisherTheHo*
- fix: add fallback gas limits to all writeContract calls (`775c47e`) — *AlexaFleisherTheHo*
- fix: frontend on port 3000 (port 80 occupied on host) (`e20dfc6`) — *AlexaFleisherTheHo*
- fix: use python3 for healthcheck (no curl in container) (`a08125d`) — *AlexaFleisherTheHo*
- fix: PORT=8766 to match docker-compose port mapping and health check (`c132fa3`) — *AlexaFleisherTheHo*
- fix: auto-route to challenge status after creation (1.5s delay to show ID) (`6af87f2`) — *AlexaFleisherTheHo*
- fix: add session race condition lock + minimum elapsed time check (`bb7829b`) — *AlexaFleisherTheHo*
- fix: reveal_times stored as relative ms from run start (not absolute epoch) (`5cf70a8`) — *AlexaFleisherTheHo*
- fix: quick-wins from Opus security review (`3e79f7e`) — *AlexaFleisherTheHo*
- fix: correct getChallenge ABI tuple to match contract struct (`ab2ef83`) — *AlexaFleisherTheHo*
- fix: invert score so higher = better (matches resolveChallenge); guard frontend compose (`1f2b514`) — *AlexaFleisherTheHo*
- fix: whitelist max 50 addrs, duplicate check, test fixes (`6093792`) — *Ubuntu*
- fix: race condition lock, round completion check, sig hex, EIP-1559 gas, token in POST body (`16df993`) — *Alexa*
- docs: fix stale NatSpec on cancelChallenge (`3473462`) — *Ubuntu*
- fix: claimTimeout status consistency, cancelChallenge griefing vector (`91ea959`) — *Ubuntu*
- fix: min wager 0.001 USDC, tie flag in ChallengeResolved event (`23eb3b9`) — *Ubuntu*

### Changed

- refactor: extract _fold_x triangle-wave helper (`d4e3b72`) — *SecretAgentAlexa*
- chore: update to v4 contract 0x26C6...532F9 — seriesLength + ELO ABI (`10dcddb`) — *bouncerpen*
- chore: update game-server ABI for sealed message mechanic (`7c44d5f`) — *AlexaFleisherTheHo*

### Removed

- remove INFRACTIONS.md — ledger lives in bouncerpen/agent-ledger (`a671a9c`) — *Ubuntu*

### Other

- docs: comment P2 predicted_ball_x_after_bounce raw svy2 intent (`39abf07`) — *SecretAgentAlexa*
- test: pytest suite for _predict_after_bounce (`89e6842`) — *SecretAgentAlexa*
- game-server: true agent-vs-agent PvP mode (closes #54) (`9946b9a`) — *SecretAgentAlexa*
- game-server: net score (player_score - ai_score) replaces raw score (#51) (`16a48a7`) — *Alexa*
- security: lock CORS to arcadeduel.org (was wildcard *) (`3ef48c0`) — *bouncerpen*
- difficulty v2: equal-speed AI + reaction delay + wider canvas + faster ball (#47) (`443bd80`) — *Alexa*
- balance: raise AI speed 65–75 → 200 px/s (#46) (`758c883`) — *Alexa*
- infra: nginx config + setup guide for arcadeduel.org (#44) (`7221b87`) — *bouncerpen*
- chore: re-pin requirements to verified working container versions (`5fea648`) — *AlexaFleisherTheHo*
- chore: move INFRACTIONS.md and NO_DIGGITY.md to agent-ledger repo (`abd5e7a`) — *Ubuntu*
- chore: restructure INFRACTIONS.md as running ledger with lessons and merits (`ca51940`) — *AlexaFleisherTheHo*
- chore: log Alexa infraction #2 (direct push to main) (`3cc9200`) — *Ubuntu*

---
*Generated by [changelog.sh](https://github.com/claude-builders-bounty/claude-builders-bounty/tree/main/skills/changelog-generator) on 2026-04-04*

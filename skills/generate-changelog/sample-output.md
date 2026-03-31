# Sample Output

Tested on a real git repo (`~/.pi/agent`) with 40+ commits across multiple contributors.

## Command run

```bash
bash changelog.sh --dry-run --version v1.1.0
```

## Output

```markdown
## [v1.1.0] — 2026-03-31

### Added

- audit descriptions + output contracts + trigger test suite (`f3af6de`)
- add claim.js — marquer bounty submitted + update seen (`7a7a5ac`)
- auto-solve CF Turnstile challenges in guardedFetch (`398fadb`)
- twitter-post.py/js — poster sur @SR_Cryptos via Brave Profile 4 sans API (`8bc10a6`)
- integrate signedFetch into guardedFetch + patch scan.js direct fetch calls (`0e9f092`)
- replace HTTP fetch with Playwright for Superteam CSR pages (`9af5e74`)
- add watch.js periodic scanner + launchd daemon (`63e76eb`)
- add Superteam Earn source + real money filter + human blocker detection (`f5085cf`)
- implement voice message handler (Telegram → Groq Whisper → Claude) (`c3da2e3`)
- add prototype-mvp A/B evals + update run-ab.js — 15/15 passing (`3d36fd4`)

### Fixed

- corriger tous les problèmes découverts lors du test Opire (`8c004bd`)
- forcer profil Fino (Profile 4) au démarrage Brave (`11efa22`)
- remplacer Chrome par Brave Browser (`79c95d1`)
- use cf_clearance cookie flow instead of header for CF Turnstile (`2996746`)
- filter fake token repos from GitHub scanner (`3192982`)
- atomic poll lock with O_EXCL to prevent duplicate pollers (`7e3e3e5`)
- race condition — generation counter prevents stale poll loops (`b6be787`)

### Changed

- slim down 7 skills + fix 2 contradictions (`57d0a8e`)
- init — snapshot initial de l'infrastructure agent (`db76c85`)
```

## Stats

- **40 commits** categorized automatically
- **0 manual edits** required
- Merge commits excluded automatically
- Conventional commits detected: `feat:`, `fix:`, `refactor:`, `chore:`
- Keyword fallback covers non-conventional commits

## Write mode (creates CHANGELOG.md)

```bash
bash changelog.sh --version v1.1.0
# ✅ CHANGELOG.md updated — 40 commits categorized (since v1.0.0)
#    Added: 22  Fixed: 12  Changed: 6  Removed: 0
```

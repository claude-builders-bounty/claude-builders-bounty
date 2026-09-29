# Changelog

_Generated from `v3.1.2-miner..HEAD`; merge commits are excluded._

## Added

- Add zh-CN market framing preamble (#8090) (`aa584b3`)
- Add mining guide link target (#8110) (`370a77c`)
- agent-to-agent on-chain transfer harness + tests (#13519) (#8115) (`660eb77`)
- add mobile touch controls to beacon atlas (#8117) (`09e7ce4`)
- add langchain-rustchain — LangChain tools for RustChain API (check_balance, list_bounties, node_health, current_epoch) [fj4WqyCCw3C5ShR1RfB7MoBPTpkRrBFYP1uT35g3MvT] (#8199) (`7c949ea`)
- add RIP-302 agent economy client (#8224) (`f90c7cb`)

## Fixed

- fail loudly on stale auto-pay lock refs (#8474) (`120d98b`)
- canonical UTXO recipients, rollback mirror cleanup, serialized hw binding (#8465) (`70454c0`)
- return 409 ACCOUNT_MIRROR_BOX_NOT_SPENDABLE again, not a misleading 400 (#8468) (`a5a2085`)
- update reqwest 0.13 rustls features and align sha2 dependency (#8095) (#8438) (`4fb014a`)
- update test_c8_adm_double_credit_poc to exercise settle_epoch_rip200 rollback (fixes #8353) (#8421) (`f76ec5a`)
- reject duplicate inputs and ensure rollback on invalid timestamp (#8413) (`610bed0`)
- validate compensated review comments (#8102) (`91f6f1a`)
- resolve macOS crashes, missing variables, and safe sys.argv sha256 fallback in install.sh (closes #16251) (#8185) (`049dcf2`)
- substring fallback must anchor to the family minimum, not whichever key matched (#8252) (`678141a`)
- let the assigned worker re-deliver a disputed job (#8257) (`b9e274a`)
- label legacy faucet.py as demo, default mock_mode off, audit config at startup (#8258) (`0062e99`)
- align time-aged multiplier docs with implementation (#7892) (#8313) (`701e9ea`)

## Changed

- bump action pin to fca66d8 (failure comments + canonical wallet regex) (#8472) (`747b9cc`)
- stop test_utxo_security_audit overwriting RC_ADMIN_KEY (unblocks CI) (#8467) (`4add40b`)
- clarify social-media bounties are not code contributions (#8107) (`5adb27a`)
- consensus-invariant harness (#8114) (`a9ffe57`)
- fix 1 typos across 6 files (wich->which, exmaple->example, thier->their, wierd->weird) (#8174) (`0599202`)
- add payout notice audit tutorial (#8307) (`926a220`)
- lock miner service templates to pass --wallet (#5713) (#8317) (`572c828`)

## Removed

- _None._

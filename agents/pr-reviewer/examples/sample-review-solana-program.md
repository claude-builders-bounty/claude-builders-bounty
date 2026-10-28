## 🤖 Claude Code PR Review

### 📋 Summary of Changes
This PR adds `tokens/token-swap/native/` — a pure Solana Native Rust implementation of a constant-product AMM, covering five instructions (CreateAmm, CreatePool, DepositLiquidity, WithdrawLiquidity, SwapExactTokensForTokens) with zero Anchor/MPL dependencies. The diff includes the Cargo workspace registration, a Mocha/litesvm TypeScript test harness, and CI/CD glue, but **the actual Rust program source (`src/`) is entirely absent from the truncated diff**, making a complete security audit impossible from this diff alone. Key architectural decisions include a `MINIMUM_LIQUIDITY` burn of 100 and a basis-point fee model bounded by `fee < 10000`.

### ⚠️ Identified Risks

- **[Security – Diff Truncation]**: The Rust program source files (`lib.rs`, instruction processors, state definitions, etc.) are not present in the provided diff. All critical security properties — PDA derivation correctness, account ownership/signer checks, CPI privilege escalation guards, and arithmetic safety — cannot be verified. This alone warrants blocking merge until a full diff is reviewed.

- **[Security – Integer Overflow in AMM Math]**: The constant-product invariant $(x + \Delta x \cdot (1 - \text{fee})) \cdot (y - \Delta y) = x \cdot y$ requires intermediate products of two `u64` values, which can overflow. Without seeing the Rust source, it is unknown whether `checked_mul`/`u128` widening is used consistently. A single unchecked multiplication on a high-liquidity pool is exploitable for fund drain.

- **[Edge Case – MINIMUM_LIQUIDITY = 100]**: Uniswap v2 uses 1000 to prevent the first liquidity provider from manipulating the price oracle via dust deposits. A value of 100 lowers this bar and may allow cheaper price inflation attacks on fresh pools, especially since LP mint decimals are fixed at 6.

- **[Edge Case – Fee Boundary `fee < 10000`]**: An AMM fee of 9999 basis points (99.99%) is technically valid per this constraint. There is no documented upper-bound intent in the PR, and the absence of a tighter `fee <= 10000 / 2` or similar sanity ceiling means malicious AMM creators can deploy near-total-fee pools that look legitimate on-chain.

- **[Stability – Only 2 Tests for Five Instructions]**: Two passing tests in 28 ms for a five-instruction AMM is a thin safety net. Notably absent: edge cases for zero-liquidity deposits, slippage rejection at the exact `min_output_amount` boundary, overflow near `u64::MAX` reserves, and fee-rounding correctness under integer truncation.

- **[Stability – Non-Frozen Lockfile in CI]**: `cicd.sh` runs `pnpm install` without `--frozen-lockfile`. On CI this can silently pull updated transitive dependencies and produce non-reproducible builds; `pnpm install --frozen-lockfile` should be used instead.

- **[Performance/Correctness – Mocha Timeout of 1,000,000 ms]**: The test script sets `-t 1000000` (≈16 min per test). While litesvm is fast, this masks slow or hanging tests and will silently absorb any test infrastructure regressions.

### 💡 Improvement Suggestions

- **[Best Practice – Request Full Diff]**: The reviewer must see all Rust source files (`tokens/token-swap/native/program/src/`) before approving. Confirm that every instruction handler validates: (a) account ownership, (b) correct PDA seeds and bump, (c) signer presence, (d) no writable system/token accounts that shouldn't be writable.

- **[Best Practice – Use `u128` for AMM Intermediate Math]**: Cast operands to `u128` before multiplying and use `checked_*` variants everywhere in the swap/deposit math, mirroring the pattern used in `spl-token-swap`. Downcast back to `u64` only after verifying the result fits.

- **[Testing – Expand Test Matrix]**: Add at minimum: (1) a swap that hits the `min_output_amount` floor exactly and one that is one lamport below (expect failure), (2) a deposit into an empty pool that triggers the `MINIMUM_LIQUIDITY` burn path vs. a proportional deposit, (3) a full withdraw that leaves the pool empty, and (4) an attempted swap with pool reserves of 0 on one side.

- **[Best Practice – Raise or Document MINIMUM_LIQUIDITY]**: Either raise to 1000 to match Uniswap v2 precedent, or add an explicit comment explaining why 100 is safe for this deployment context (e.g., token decimals guarantee sufficient precision).

- **[Refactor – Add Fee Upper-Bound Check]**: Change `fee < 10000` to `fee < 10000 && fee <= 1000` (10%) or at minimum document the intended ceiling and reject obvious griefing values with a named error (`InvalidFee`).

- **[Architecture – Pin CI Dependencies]**: Replace `pnpm install` with `pnpm install --frozen-lockfile` in `cicd.sh` to guarantee reproducible test runs across environments.

### 🎯 Confidence Score
**Confidence: Low**

The Rust program source — the highest-risk component in any on-chain AMM — is entirely absent from the provided diff due to truncation, making it impossible to verify account validation, arithmetic safety, or CPI correctness. The review above covers structural and logic risks inferrable from the PR description and metadata only; a full audit requires the complete `src/` tree.
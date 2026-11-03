### 🤖 Claude PR Review

## Summary
This PR wraps the contexts that `_resolve_context` creates in `with` blocks. That way they are closed after shell completion, so `click.File` handles no longer leak and raise `ResourceWarning`. It also updates the `Context.exit` docstring and the changelog. It adds one test that runs completion on a group with a `click.File` option.

## Risks
- **Wrong args in the non-chain branch.** `args = ctx._protected_args + ctx.args` now runs before `ctx = sub_ctx`, so it reads the parent's leftover args, not the new subcontext's. The original code read them after reassigning `ctx`. Nested groups (`cli group sub <TAB>`) will resolve the wrong command or loop on stale args.
- **Wrong args in the chain branch.** `args = sub_ctx.args` runs before `sub_ctx = sub_sub_ctx`, so it reads the previous context's args. Chained commands can resolve incorrectly. The inner `while args` loop could also fail to make progress, because `args` is the stale value.
- **The returned context is already closed.** The `with` blocks exit as soon as `ctx = sub_ctx` is assigned, and the root `with` exits on `return ctx`. `_resolve_context` therefore returns a closed context. `get_completions` then calls `param.shell_complete(ctx, ...)` and `ctx.command.shell_complete` on it. Custom completion callbacks that use `ctx.obj`, `with_resource` resources or `call_on_close` state may see torn-down state. Any other caller of `_resolve_context` is affected the same way.
- **Test coverage is weak.** The test only uses a group with no subcommands, so the nested and chained paths changed here are never run. That is why the bugs above go unnoticed. The "no warnings to start" assertion is trivial. `ResourceWarning` is emitted at garbage collection, so without `gc.collect()` the final assertion can pass even when files leak, which makes it flaky or vacuous.
- **Changelog wording.** The entry has the `ResourceWarning`s plural rendered inside double backticks, which is awkward in RST.

## Suggestions
- Restructure so the contexts stay open while completion runs. For example, make `_resolve_context` a context manager or generator, or have `get_completions` enter an `ExitStack` and register each created context on it. Alternatively, return the contexts and close them in the caller after completions are collected.
- Compute `args` from the new context, as the original code did (`args = sub_ctx._protected_args + sub_ctx.args`). In the chain branch, use `sub_sub_ctx.args`.
- Add tests for a nested group, a chained group, and a subcommand that has a `click.File` option. Each should check that the right completions are returned.
- Add a test with a custom `shell_complete` that touches `ctx.obj` or a `with_resource` resource, to confirm the context is still usable.
- In the test, call `gc.collect()` inside the `catch_warnings` block, and use `simplefilter("always", ResourceWarning)`. Assert specifically on `ResourceWarning`. Drop the redundant initial assertion.

## Confidence
High. The two argument-ordering mistakes and the early close of the returned context are visible directly in the diff.

---
_Automated review of https://github.com/pallets/click/pull/2800 by claude-review. Verify before acting._

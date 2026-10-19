## Summary
This PR bumps PyO3 from 0.29.2 to 0.30.1 and uses the new native `PyFrozenDict` type. The runtime `builtins.frozendict` lookups are replaced with a `cfg(Py_3_15)` shim in `common/frozendict.rs`. The PR also drops now-redundant workarounds: `skip_from_py_object`, the custom `py_get_attrs`, and `cast_unsigned`. It matters because it removes the TODOs tied to PyO3#6174 and #5985 and makes frozendict handling cheaper and type-safe. It is also a dependency bump, and it pulls in a new major version of `syn` (3.x).

## Risks
- **Compile-time vs runtime frozendict detection.** Availability is now decided by the `Py_3_15` cfg at build time, not by `getattr(builtins, "frozendict")` at import. If any wheel is built with `abi3` (or against a PyO3 config that doesn't set `Py_3_15`) and then run on 3.15, frozendict schemas will fail with "only available on Python 3.15 and above". Conversely, a 3.15 build running on an older interpreter is not possible, so that direction is fine. Confirm the wheel matrix builds per-interpreter for 3.15.
- **`PyFrozenDict::from_sequence(mapping)` is passed a `dict`.** The name implies a sequence of pairs. If it doesn't accept a mapping, every frozendict validation, and every serialization in Python mode, will break. This is the main correctness question and the Python-side tests only catch it on a 3.15 CI job.
- **Ordering dependency.** The description says "Needs pydantic#13806", so merging before that PR lands may break the build or the Python side. The checklist is entirely unticked and there is no linked issue.
- **Supply chain and toolchain.** `syn 2.0.82` becomes `syn 3.0.6` for the macros crates. This is a new major in the proc-macro tree, so check MSRV (1.88) and compile-time impact on all targets, including PyPy and the musl, Windows and wasm builds.
- **Removed `skip_from_py_object` across about 15 pyclasses.** This is only safe if 0.30 no longer derives `FromPyObject` for `Clone` pyclasses by default. If it still does, these classes (for example `ValidationError` and `PyUrl`) gain an implicit by-value extraction. Any code path relying on the old opt-out behavior would change silently rather than fail to compile.
- **`getattr_opt` replaces `py_get_attrs`.** The semantics should match (only `AttributeError` is swallowed), but it sits on hot paths (`__pydantic_serializer__` lookup, attribute-based `from_attributes` validation). Benchmark it and run the from-attributes tests.
- **Dead `Err` path.** On non-3.15 builds `new_frozendict` and `frozendict_items` return `RuntimeError`. These are unreachable only because the validator and serializer builders reject the schema first, and `ObType::Frozendict` never matches since the raw type is `0`. A future caller that skips those guards would hit a runtime error.

## Suggestions
- Add or confirm a Rust or Python test on 3.15 that covers frozendict subclass validation, serialization in python, json and inference modes, and round-tripping a nested frozendict. Run it in CI on 3.15, since 3.15 is the only interpreter that exercises the new code.
- Verify `from_sequence` accepts a `dict`. If it doesn't, use the proper constructor (for example a mapping-based `PyFrozenDict::new`) and update the doc comment on `new_frozendict` to match.
- Replace the `0` sentinel and the `FROZENDICT_AVAILABLE` const with a single `Option`/`cfg`-based API, or use a `const fn`/`#[cfg]` guard, so the unreachable `Err` branches don't ship in non-3.15 builds.
- Fill in the PR description with a changelog-worthy title and body. Note the PyO3 0.30 migration items (the `FromPyObject` default change, `syn` 3) and link the upstream PRs.
- Run clippy with `-D warnings` on 3.9 to 3.15 to catch unused-import or unused-variable fallout from the cfg gating (for example the `py` binding in `ob_type.rs`).
- Confirm with `cargo tree` that no other crate in the workspace still pulls `syn 2` or PyO3 0.29, and that `pyo3-build-config` stays aligned across build and dev dependencies.

## Confidence
Medium: the diff is mostly mechanical and internally consistent, but I couldn't compile it or check PyO3 0.30 API details such as the `from_sequence` signature and the `FromPyObject` default.

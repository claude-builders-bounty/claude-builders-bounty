# Sample review: adamtheturtle/strict-kwargs#201

> Subject: fix(ty): pin ty server cwd to project root for reproducible resolution (#200)
> Author: Guciolek
> Files changed: 1 (src/ty_resolver.rs, +6 / -1)

## 🤖 Claude Code Review

### Summary
The PR pins the `ty server` subprocess working directory to the project root inside `TyResolver::start` by adding `.current_dir(project_root)` to the existing `Command` builder. The change is minimal, surgical, and includes a clear comment explaining the rationale and linking the originating issue.

### ⚠️ Risks
- The added `current_dir` does not validate that `project_root` is absolute. If a caller passes a relative path, the spawned server's `cwd` is resolved against the **caller's** cwd, partially defeating the fix.
- Behavioural test gap: the existing test suite does not exercise the new `current_dir` call. A test that spawns the resolver and asserts the child process's `cwd` (e.g. via `/proc/<pid>/cwd` on Linux or `lsof` on macOS) would lock the fix in.

### 💡 Suggestions
- In `TyResolver::start`, call `std::path::absolute(project_root)` (mirroring the existing pattern in `initialize_params` at line 115) before passing it to `.current_dir(...)`. This makes the change robust to relative `project_root` arguments.
- Add a `#[test]` that confirms the child is spawned with the right cwd. This can be unit-tested without `ty` by reading the constructed `Command` (you may need a small refactor to expose the `Command` builder for testability).

**Confidence:** `High`

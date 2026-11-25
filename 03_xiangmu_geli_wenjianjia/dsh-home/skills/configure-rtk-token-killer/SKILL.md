---
name: configure-rtk-token-killer
description: Use when installing RTK token-saver CLI for Hermes.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [rtk, tokens, terminal, windows, plugin]
    related_skills: [hermes-agent, provider-endpoint-quirks]
---

# Configure RTK (Rust Token Killer) for Hermes

## When to Use

Load this skill when the user asks to install, configure, fix, or verify RTK
("Rust Token Killer") for Hermes on Windows — including cases where the
`rtk-rewrite` plugin appears enabled but terminal commands are not being
rewritten.

RTK rewrites terminal commands (`git status` → `rtk git status`) so the model sees
compact output instead of raw spam. Hermes integrates it via the community plugin
`rtk-rewrite`, which installs a `pre_tool_call` hook.

## Steps

1. Install the binary:
   ```bash
   winget install rtk          # package id: rtk-ai.rtk
   ```
   winget adds the **Packages** dir (not the Links dir) to the user PATH and also
   creates a Links alias. Real path:
   `C:\Users\<user>\AppData\Local\Microsoft\WinGet\Packages\rtk-ai.rtk_*\rtk.exe`

2. Install + enable the plugin:
   ```bash
   hermes plugins install rtk-rewrite   # community, catalog:community
   hermes plugins enable rtk-rewrite
   ```
   Plugin lands in `<hermes_root>/plugins/rtk-rewrite` (NOT `~/AppData/Local/hermes/plugins/`).

3. **Fix the PATH-reload pitfall** (the important one, see below), then verify.

## Pitfall: running Hermes process never reloads winget's PATH change

The plugin resolves the binary with `shutil.which("rtk")` at registration time.
winget updates the *persistent* user PATH, but a **Hermes process already running**
keeps its old environment → `which("rtk")` is None → hook is never registered →
plugin silently does nothing (fail-open, no error).

Fix — put `rtk.exe` on a directory that is **both** on the persistent PATH and
already loaded in the current process, e.g. the Hermes bin dir:
```bash
cp "/c/Users/<user>/AppData/Local/Microsoft/WinGet/Packages/rtk-ai.rtk_*/rtk.exe" \
   "/d/Ai/Agent/hermes/bin/rtk.exe"     # <hermes_root>/bin is on PATH
```
A full Hermes restart also fixes it, but the copy avoids needing one.

**No restart needed if you re-trigger discovery.** Run
`hermes plugins disable rtk-rewrite && hermes plugins enable rtk-rewrite`.
That forces `discover_plugins(force=True)`, which **purges the plugin's
`sys.modules` entries and re-imports it** — so the module-level
`_rtk_available` cache resets and the hook registers live. `enable` prints
`Gateway reloaded plugins — active in the running gateway now: hooks` on
success. The running desktop/gateway process then rewrites terminal commands
immediately, no app restart required.

## Pitfall: GBK `UnicodeDecodeError` / mojibake on Windows (plugin bug)

The upstream community plugin calls `subprocess.run(..., text=True)` **without**
`encoding=`. On Windows the default locale codec is GBK/cp936 while rtk emits
UTF-8, so a rewrite whose output contains non-ASCII bytes either:

- **mojibakes** the rewritten command (visible corruption, garbled path executed), or
- raises `UnicodeDecodeError` in the reader thread → `result.stdout` becomes
  `None` → the plugin logs `hermes plugin warning: 'NoneType' object has no attribute 'strip'`
  and silently passes the command through unrewritten.

Tell-tale log line: `[gateway-crash] thread ... (_readerthread) raised
UnicodeDecodeError: 'gbk' codec can't decode byte ...` immediately followed by
the plugin warning.

Fix — add to the `subprocess.run` call in `plugins/rtk-rewrite/__init__.py`:
```python
                encoding="utf-8",
                errors="replace",
```
Then re-trigger discovery (disable+enable) so the patched module is re-imported.
Note: this makes the plugin's git working tree dirty; `hermes plugins update`
will clobber the fix — re-apply after updating, or report upstream.

Reproduce under GBK with `PYTHONUTF8=0 <python> ...`; a normal UTF-8 shell will
NOT reproduce it (which is why it hides until it bites in the real process).

## Verification (do all of these, don't assume)

```bash
# 1. binary works
<hermes_root>/bin/rtk.exe --version
# 2. resolution + rewrite return codes, using Hermes's own python
<hermes_root>/tools/python-*/python.exe -c "import shutil,subprocess; print(shutil.which('rtk')); print(subprocess.run(['rtk','rewrite','git status'],capture_output=True,text=True).returncode)"
#    rc=3 or 0 -> will rewrite ; rc=1 or 2 -> passthrough (expected for npm/echo)
# 3. plugin registered its hook
hermes plugins doctor rtk-rewrite      # expect: OK, 1 hook(s)
```

## Notes

- `hermes plugins enable` says "Takes effect on next session" — start a **new chat**
to activate interception (no full app restart needed once `rtk.exe` is on a loaded PATH).
- `[rtk] No hook installed — run rtk init -g` is a **Claude Code** prompt, unrelated to
  Hermes. Ignore it; Hermes uses the plugin hook, not `~/.claude/settings.json`.
- `hermes plugins list` merges bundled plugins; a bundled `kanban` showing alongside
  `rtk-rewrite` in an old record is normal.
- `rtk gain --history` shows cumulative token savings (empty on a fresh install).

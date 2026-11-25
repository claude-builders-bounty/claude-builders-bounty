# Exact Patch Diffs for cua_backend.py (Hermes 0.20.x)

## Patch 1: Manifest Check Timeout

**File**: `tools/computer_use/cua_backend.py`
**Function**: `cua_driver_runtime_contract_status`
**Lines**: ~1056-1065

```diff
--- a/tools/computer_use/cua_backend.py
+++ b/tools/computer_use/cua_backend.py
@@ -1053,7 +1053,19 @@ def cua_driver_runtime_contract_status(binary: Optional[str] = None) -> Dict[s
     try:
         from tools.environments.local import _sanitize_subprocess_env
 
+        # WSL2 running Windows binary via interop needs more time for cold start
+        # Detect WSL2: /proc/version contains "microsoft"
+        is_wsl2 = False
+        if sys.platform == "linux":
+            try:
+                with open("/proc/version", encoding="utf-8") as f:
+                    if "microsoft" in f.read().lower():
+                        is_wsl2 = True
+            except Exception:
+                pass
+        manifest_timeout = 15.0 if sys.platform == "win32" else (120.0 if is_wsl2 else 5.0)
+
         result = subprocess.run(
             [resolved, "manifest"],
             capture_output=True,
             text=True,
             encoding="utf-8",
             errors="replace",
-            timeout=15.0 if sys.platform == "win32" else 5.0,
+            timeout=manifest_timeout,
             stdin=subprocess.DEVNULL,
             env=_sanitize_subprocess_env(cua_driver_child_env()),
             creationflags=windows_hide_flags(),
         )
```

## Patch 2: MCP Session Startup Timeout

**File**: `tools/computer_use/cua_backend.py`
**Class**: `_CuaDriverSession`
**Method**: `_start_lifecycle_locked`
**Lines**: ~1764

```diff
--- a/tools/computer_use/cua_backend.py
+++ b/tools/computer_use/cua_backend.py
@@ -1761,7 +1761,16 @@ class _CuaDriverSession:
         self._lifecycle_future = asyncio.run_coroutine_threadsafe(
             self._lifecycle_coro(), loop
         )
-        if not self._ready_event.wait(timeout=30.0):
+        # Detect WSL2 for longer timeout
+        is_wsl2 = False
+        if sys.platform == "linux":
+            try:
+                with open("/proc/version", encoding="utf-8") as f:
+                    if "microsoft" in f.read().lower():
+                        is_wsl2 = True
+            except Exception:
+                pass
+        if not self._ready_event.wait(timeout=30.0 if not is_wsl2 else 120.0):
             # Best-effort: signal shutdown if the future is still alive.
             self._signal_shutdown_locked()
```

## Why These Values?

| Scenario | Cold Start Time | Configured Timeout |
|----------|-----------------|-------------------|
| Windows native `cua-driver.exe manifest` | ~1-2s | 15s (default) |
| WSL2 interop `cua-driver.exe manifest` (first call) | ~60-90s (Defender scan) | **120s** |
| WSL2 interop `cua-driver.exe manifest` (subsequent) | ~1s | 120s (safe ceiling) |
| MCP session startup (Windows native) | ~5-10s | 30s (default) |
| MCP session startup (WSL2 interop) | ~60-90s | **120s** |

## Applying the Patches

```bash
cd /home/user01/.hermes/hermes-agent
# Apply both patches
patch -p1 < /home/user01/.hermes/skills/devops/wsl2-windows-interop-automation/references/cua_backend_patches.md
```

> **Note**: These patches target Hermes 0.20.x (`cua_backend.py` from NousResearch/hermes-agent). Line numbers may shift in future versions — search for the function names if patches don't apply cleanly.
## 🤖 claude-review

**PR:** https://github.com/python/cpython/pull/125000
**Title:** gh-123961: make `curses` global flags free-threaded friendly

### Summary
This PR makes the curses module's global state (setupterm/initscr/start_color flags and screen encoding) thread-safe under the free-threaded build (Py_GIL_DISABLED) by introducing atomic accessor functions, and adds a guard to prevent the module from being loaded more than once per process. It also renames internal check functions and updates the globals-to-fix list.

### Identified Risks

- [MED] The new module-load guard uses a plain static int and atomic operations only under Py_GIL_DISABLED; in the GIL build, it is not atomic, but since module exec is serialized by the import lock, this is likely safe. However, if the module is ever loaded concurrently in a subinterpreter scenario without the GIL, this could race.
- [MED] The atomic pointer load/store for curses_screen_encoding uses _Py_atomic_load_ptr/_Py_atomic_store_ptr, but the pointer is a const char* and the store casts away const. This is fine for atomicity but the memory pointed to must remain valid; if the encoding string is freed or mutated after being set, this could cause use-after-free. The diff does not show any change to the lifetime management of the encoding string.
- [LOW] The new module-load guard sets curses_module_loaded to 1 before the module initialization completes. If initialization fails after this point, the module cannot be re-imported in the same process, which might be unexpected. Consider setting the flag only after successful initialization.

### Improvement Suggestions

- Consider using _Py_atomic_int for curses_module_loaded and the other flags even in the GIL build to avoid conditional compilation and potential future issues.
- Ensure that the encoding string stored via curses_set_screen_encoding is kept alive for the lifetime of the module (e.g., by storing a copy or managing reference counts).
- Move the setting of curses_module_loaded to the end of cursesmodule_exec, after all initialization steps have succeeded, to avoid blocking re-import after a partial failure.

**Confidence:** Medium

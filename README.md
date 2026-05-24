# Kernel-Level Bash Security Hook

This module implements an ultra-secure, hybrid security hook to safely intercept and execute user-provided bash commands. It guarantees protection against destructive commands (e.g. `rm -rf /`), remote code execution pipelines (`curl | sh`), and fork bombs.

## How it works

The architecture is divided into two robust phases:

### Phase 1: Static AST Parsing & Allowlisting (Python)
- **AST Parsing:** Uses `bashlex` to construct an Abstract Syntax Tree of the command string. This defeats obfuscation techniques (like `r""m -r''f /` or string concatenation bypasses).
- **Multi-layer Decoding:** Identifies and decodes Base64/Hex payloads before parsing, stopping obfuscated execution strings.
- **Strict Allowlist Policy:** Rather than blacklisting known bad commands, the parser uses a strict **Allowlist** (`ls`, `echo`, `cat`, etc.). Any command outside this list is immediately blocked.
- **Recursive Inspection:** Blocks shell function definitions recursively to kill fork bombs.

### Phase 2: Kernel-Level Sandboxing (Bubblewrap)
If a command passes the strict AST checks, it is NOT executed natively. Instead, the hook generates a secure execution string that wraps the command in a Linux kernel-level sandbox (`bwrap`):
- **User Namespace Isolation:** Command runs completely isolated from the host PID and IPC spaces (`--unshare-all`).
- **Network/File Capability Control:** The network stack is disconnected. The root filesystem is mounted entirely **Read-Only** (`--ro-bind / /`).
- **Ephemeral Execution:** Critical directories (`/tmp`, `/home`) are mounted as temporary RAM disks (`--tmpfs`). Any changes disappear immediately after execution.
- **Syscall Restriction Ready:** Ready to attach seccomp-bpf filters to restrict low-level kernel syscalls.

## Usage
```python
from security_hook import prepare_secure_execution, SecurityException

cmd = "ls -la"
try:
    safe_sandbox_cmd = prepare_secure_execution(cmd)
    # Outputs: bwrap --unshare-all --ro-bind / / --tmpfs /tmp ... bash -c 'ls -la'
except SecurityException as e:
    print("Blocked:", e)
```

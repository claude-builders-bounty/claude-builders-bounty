# Autonomous Security Scanner Agent for Claude Code 🛡️

A purpose-built Claude Code extension agent that audits codebases for critical vulnerabilities before PRs and deployments.

## Detected Vulnerability Classes
- **SEC-001 (High)**: Leaked API keys, JWTs, AWS credentials, and private keys.
- **SEC-002 (High)**: Unsafe shell command execution (`subprocess` with `shell=True`, `os.system`).
- **SEC-003 (Medium)**: SQL Injection patterns via string formatting.
- **SEC-004 (High)**: Insecure deserialization via `pickle` or untrusted `yaml.load`.
- **SEC-005 (Critical)**: Dynamic code evaluation via `eval()` or `exec()`.

## Installation & Usage

```bash
# Direct run on any project
python agents/security-scanner/security_scanner.py .

# Output machine-readable JSON for CI/CD gates
python agents/security-scanner/security_scanner.py . --json
```

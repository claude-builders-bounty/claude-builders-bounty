"""Risk and suggestion regex heuristics for claude-review."""
from __future__ import annotations

RISK_PATTERNS = [
    (r"\brm\s+(-[^\s]*f[^\s]*|--force)", "Forceful rm in shell/scripts"),
    (r"\beval\s*\(", "Use of eval()"),
    (r"child_process|subprocess\.(call|Popen|run)", "Process spawning / shell exec"),
    (r"\b(password|secret|api[_-]?key|private[_-]?key)\b\s*[:=]", "Possible credential literal"),
    (r"AKIA[0-9A-Z]{16}", "Looks like AWS access key id"),
    (r"-----BEGIN (RSA |OPENSSH )?PRIVATE KEY-----", "Private key material"),
    (r"\bsudo\b", "Elevated privilege (sudo)"),
    (r"DROP\s+TABLE|TRUNCATE\s+", "Destructive SQL"),
    (r"git\s+push\s+.*--force", "Force-push"),
    (r"chmod\s+777|umask\s+0", "Overly permissive file mode"),
    (r"innerHTML\s*=", "XSS risk via innerHTML"),
    (r"dangerouslySetInnerHTML", "React dangerouslySetInnerHTML"),
    (r"pickle\.loads|yaml\.load\(", "Unsafe deserialization"),
    (r"verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*0", "TLS verification disabled"),
]

SUGGEST_PATTERNS = [
    (r"\bTODO\b|\bFIXME\b|\bXXX\b", "Resolve leftover TODO/FIXME markers before merge"),
    (r"console\.log\(|(?<!\w)print\(", "Trim debug logging from production paths"),
    (r":\s*any\b|as any\b", "Tighten TypeScript `any` where practical"),
    (r"eslint-disable|noqa:|@ts-ignore|@ts-expect-error", "Avoid blanket lint/type suppressions without rationale"),
    (r"raise NotImplementedError|throw new Error\(['\"]not implemented", "Fill stubbed implementations"),
]

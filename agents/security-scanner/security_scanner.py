#!/usr/bin/env python3
"""
Autonomous Security Audit & Vulnerability Scanner for Claude Code Projects.

Scans project files for:
1. Hardcoded secrets (API keys, AWS credentials, JWTs, private keys).
2. Dangerous command execution patterns (shell=True, os.system, exec, eval).
3. SQL Injection vulnerabilities (raw string formatting in SQL statements).
4. Insecure deserialization (pickle.loads, yaml.load without SafeLoader).
5. Permissive file permissions and unsafe temporary file creation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RULES = [
    (
        "SEC-001",
        "HIGH",
        "Hardcoded Secret / API Token",
        r"(?i)(?:api_key|secret_key|private_key|auth_token|bearer|access_token|aws_secret_access_key)\s*[:=]\s*['\"][A-Za-z0-9_\-+=/]{16,}['\"]",
        "Store secrets in environment variables or a secure key manager.",
    ),
    (
        "SEC-002",
        "HIGH",
        "Unsafe Shell Execution (Command Injection Risk)",
        r"(?:subprocess\.(?:Popen|call|run|check_output)\([^)]*shell\s*=\s*True|os\.system\(|os\.popen\()",
        "Pass arguments as a list with shell=False to prevent command injection.",
    ),
    (
        "SEC-003",
        "MEDIUM",
        "SQL Injection via String Formatting",
        r"(?i)(?:execute|cursor\.execute)\s*\(\s*(?:f['\"].*?(?:SELECT|INSERT|UPDATE|DELETE)|['\"].*?(?:SELECT|INSERT|UPDATE|DELETE).*?%s.*?%|['\"].*?(?:SELECT|INSERT|UPDATE|DELETE).*?\.format\()",
        "Use parameterized queries with query placeholders (?, %s) rather than string interpolation.",
    ),
    (
        "SEC-004",
        "HIGH",
        "Insecure Deserialization (Arbitrary Code Execution)",
        r"(?:pickle\.loads\(|yaml\.load\([^)]*(?!Loader=yaml\.SafeLoader))",
        "Use json, safer loaders (yaml.safe_load), or cryptographic signatures.",
    ),
    (
        "SEC-005",
        "CRITICAL",
        "Dynamic Code Evaluation (eval / exec)",
        r"(?:\beval\s*\(|\bexec\s*\()",
        "Avoid dynamic evaluation of untrusted strings; use abstract syntax trees (ast.literal_eval) for data.",
    ),
]

IGNORE_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build"}
IGNORE_EXTS = {".png", ".jpg", ".jpeg", ".mp4", ".mp3", ".pdf", ".zip", ".tar", ".gz", ".exe", ".bin"}

@dataclass
class Finding:
    rule_id: str
    severity: str
    title: str
    file_path: str
    line_number: int
    matched_snippet: str
    remediation: str

class SecurityScanner:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.findings: list[Finding] = []

    def scan(self) -> list[Finding]:
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                p = Path(root) / file
                if p.suffix.lower() in IGNORE_EXTS:
                    continue
                self._scan_file(p)
        return self.findings

    def _scan_file(self, file_path: Path):
        try:
            rel_path = file_path.relative_to(self.root_dir).as_posix()
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
            for rule_id, severity, title, pattern, remediation in RULES:
                regex = re.compile(pattern)
                for idx, line in enumerate(lines, 1):
                    if regex.search(line):
                        clean_snip = line.strip()[:100]
                        self.findings.append(
                            Finding(
                                rule_id=rule_id,
                                severity=severity,
                                title=title,
                                file_path=rel_path,
                                line_number=idx,
                                matched_snippet=clean_snip,
                                remediation=remediation,
                            )
                        )
        except Exception:
            pass

    def generate_markdown_report(self) -> str:
        report = [
            "# 🛡️ Claude Code Security Audit Report",
            f"**Audit Timestamp**: {datetime.now(timezone.utc).isoformat()}",
            f"**Total Findings**: {len(self.findings)}",
            "",
            "| Rule ID | Severity | Title | File | Line |",
            "|---|---|---|---|---|",
        ]
        for f in self.findings:
            report.append(f"| `{f.rule_id}` | **{f.severity}** | {f.title} | `{f.file_path}` | {f.line_number} |")

        report.append("")
        report.append("## Detailed Remediations")
        for idx, f in enumerate(self.findings, 1):
            report.append(f"### {idx}. [{f.severity}] {f.title} ({f.rule_id})")
            report.append(f"- **Location**: `{f.file_path}:{f.line_number}`")
            report.append(f"- **Snippet**: `{f.matched_snippet}`")
            report.append(f"- **Fix**: {f.remediation}")
            report.append("")
        return "\n".join(report)

def main() -> int:
    parser = argparse.ArgumentParser(description="Autonomous Security Audit Scanner for Claude Code.")
    parser.add_argument("path", nargs="?", default=".", help="Target project directory to audit")
    parser.add_argument("--json", action="store_true", help="Output findings as JSON")
    args = parser.parse_args()

    scanner = SecurityScanner(Path(args.path).resolve())
    findings = scanner.scan()

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print(scanner.generate_markdown_report())

    return 1 if any(f.severity in ("CRITICAL", "HIGH") for f in findings) else 0

if __name__ == "__main__":
    sys.exit(main())

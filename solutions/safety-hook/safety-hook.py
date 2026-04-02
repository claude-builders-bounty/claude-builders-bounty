#!/usr/bin/env python3
"""
Pre-tool-use safety hook - blocks destructive bash commands.

Designed as a drop-in hook for LLM tool-use pipelines (Copilot, LangChain,
OpenAI function-calling, etc.).  It inspects the command string *before*
execution and returns an ALLOW / BLOCK verdict with a human-readable report.

Architecture
------------
1. Normalisation - collapse whitespace, expand common obfuscation tricks.
2. Rule matching - regex rules from hook-config.yaml, each with a
   severity that maps to a base score.
3. Allowlisting - per-rule allowlist regexes suppress false positives.
4. Compound modifiers - contextual signals (sudo, --no-preserve-root,
   output suppression) add extra points on top of any triggered rule.
5. Verdict - total score >= threshold -> BLOCK.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import yaml

_HERE = Path(__file__).resolve().parent
_DEFAULT_CONFIG = _HERE / "hook-config.yaml"
_DEFAULT_THRESHOLD = 100

SEVERITY_DEFAULTS: Dict[str, int] = {
    "critical": 100,
    "high": 70,
    "medium": 40,
    "low": 20,
}


@dataclass
class RuleHit:
    """A single rule that matched the command."""
    rule_id: str
    severity: str
    score: int
    message: str


@dataclass
class ModifierHit:
    """A compound modifier that fired."""
    score: int
    message: str


@dataclass
class EvalResult:
    """Full evaluation result for one command."""
    command: str
    blocked: bool
    total_score: int
    threshold: int
    rule_hits: List[RuleHit] = field(default_factory=list)
    modifier_hits: List[ModifierHit] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        return "BLOCK" if self.blocked else "ALLOW"

    def report(self, verbose: bool = True) -> str:
        lines = [
            f"[{self.verdict}] score={self.total_score}/{self.threshold}",
            f"  command: {self.command!r}",
        ]
        if verbose:
            for rh in self.rule_hits:
                lines.append(
                    f"  W [{rh.severity.upper():>8}] +{rh.score:3d}  "
                    f"{rh.message}  (rule: {rh.rule_id})"
                )
            for mh in self.modifier_hits:
                lines.append(f"  +          +{mh.score:3d}  {mh.message}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "blocked": self.blocked,
            "score": self.total_score,
            "threshold": self.threshold,
            "command": self.command,
            "rule_hits": [
                {"id": r.rule_id, "severity": r.severity,
                 "score": r.score, "message": r.message}
                for r in self.rule_hits
            ],
            "modifier_hits": [
                {"score": m.score, "message": m.message}
                for m in self.modifier_hits
            ],
        }


def normalise_command(cmd: str) -> str:
    """Collapse whitespace and decode common obfuscation patterns."""
    cmd = cmd.strip()
    cmd = re.sub(r"[ \t]+", " ", cmd)

    def _hex_sub(m: re.Match) -> str:
        try:
            return bytes.fromhex(m.group(1)).decode("ascii")
        except Exception:
            return m.group(0)
    cmd = re.sub(r"\\x([0-9a-fA-F]{2})", _hex_sub, cmd)

    def _oct_sub(m: re.Match) -> str:
        try:
            return chr(int(m.group(1), 8))
        except Exception:
            return m.group(0)
    cmd = re.sub(r"\\([0-7]{3})", _oct_sub, cmd)

    cmd = re.sub(r"(?<=[a-zA-Z])\'\'(?=[a-zA-Z])", "", cmd)
    cmd = re.sub(r'(?<=[a-zA-Z])""(?=[a-zA-Z])', "", cmd)
    cmd = cmd.replace("\\\n", "")
    return cmd


def extract_subcommands(cmd: str) -> List[str]:
    """Split on shell meta-characters to get individual subcommands."""
    parts = re.split(r"\s*(?:\n|;|&&|\|\||(?<!\$)\|)\s*", cmd)
    subshells = re.findall(r"\$\(([^)]+)\)", cmd) + re.findall(r"`([^`]+)`", cmd)
    return [p.strip() for p in parts + subshells if p.strip()]


class SafetyHook:
    """Evaluate bash commands against a configurable rule set."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        cfg_path = Path(config_path) if config_path else _DEFAULT_CONFIG
        if cfg_path.exists():
            with open(cfg_path) as fh:
                self._cfg: Dict[str, Any] = yaml.safe_load(fh)
        else:
            self._cfg = {}

        self.threshold: int = self._cfg.get("threshold", _DEFAULT_THRESHOLD)
        sev = {**SEVERITY_DEFAULTS, **self._cfg.get("severity_scores", {})}
        self._severity_scores = sev

        self._rules: List[Dict[str, Any]] = []
        for r in self._cfg.get("rules", []):
            compiled = {
                "id": r["id"],
                "regex": re.compile(r["pattern"], re.IGNORECASE),
                "severity": r["severity"],
                "score": sev[r["severity"]],
                "message": r["message"],
                "allowlist": [
                    re.compile(a, re.IGNORECASE)
                    for a in r.get("allowlist", [])
                ],
            }
            self._rules.append(compiled)

        self._modifiers: List[Dict[str, Any]] = []
        for m in self._cfg.get("compound_modifiers", []):
            self._modifiers.append({
                "regex": re.compile(m["pattern"], re.IGNORECASE),
                "score": m["score"],
                "message": m["message"],
            })

    def evaluate(self, command: str) -> EvalResult:
        """Evaluate command and return an EvalResult."""
        normalised = normalise_command(command)

        targets = [normalised] + extract_subcommands(normalised)
        seen: set = set()
        unique_targets: list = []
        for t in targets:
            if t not in seen:
                seen.add(t)
                unique_targets.append(t)

        rule_hits: List[RuleHit] = []
        hit_ids: set = set()

        for target in unique_targets:
            for rule in self._rules:
                if rule["id"] in hit_ids:
                    continue
                if not rule["regex"].search(target):
                    continue
                if any(al.search(target) for al in rule["allowlist"]):
                    continue
                rule_hits.append(RuleHit(
                    rule_id=rule["id"],
                    severity=rule["severity"],
                    score=rule["score"],
                    message=rule["message"],
                ))
                hit_ids.add(rule["id"])

        modifier_hits: List[ModifierHit] = []
        if rule_hits:
            for mod in self._modifiers:
                if mod["regex"].search(normalised):
                    modifier_hits.append(
                        ModifierHit(score=mod["score"], message=mod["message"])
                    )

        total = sum(r.score for r in rule_hits) + sum(m.score for m in modifier_hits)
        blocked = total >= self.threshold

        return EvalResult(
            command=command,
            blocked=blocked,
            total_score=total,
            threshold=self.threshold,
            rule_hits=rule_hits,
            modifier_hits=modifier_hits,
        )

    def evaluate_tool_call(self, payload: Dict[str, Any]) -> EvalResult:
        """Accept a tool-call dict. Only bash-like tools are inspected."""
        tool = payload.get("tool", "").lower()
        if tool not in ("bash", "shell", "terminal", "run_command", "execute"):
            return EvalResult(
                command=f"<non-bash tool: {tool}>",
                blocked=False,
                total_score=0,
                threshold=self.threshold,
            )
        cmd = (payload.get("command", "")
               or payload.get("cmd", "")
               or payload.get("input", ""))
        return self.evaluate(cmd)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pre-tool-use safety hook - blocks destructive bash commands."
    )
    parser.add_argument("command", nargs="?", help="Command string to evaluate")
    parser.add_argument(
        "--json", action="store_true",
        help="Read JSON tool-call from stdin instead of positional arg",
    )
    parser.add_argument("--config", "-c", default=None, help="Path to config YAML")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Only print verdict line")
    parser.add_argument("--json-output", "-j", action="store_true",
                        help="Output result as JSON")
    args = parser.parse_args(argv)

    hook = SafetyHook(config_path=args.config)

    if args.json:
        payload = json.load(sys.stdin)
        result = hook.evaluate_tool_call(payload)
    elif args.command:
        result = hook.evaluate(args.command)
    else:
        parser.print_help()
        return 2

    if args.json_output:
        json.dump(result.to_dict(), sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(result.report(verbose=not args.quiet))

    return 1 if result.blocked else 0


if __name__ == "__main__":
    sys.exit(main())

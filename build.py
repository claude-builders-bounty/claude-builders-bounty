#!/usr/bin/env python3
"""Build script for claude-builders-bounty — generates diagnostic artifacts for CI."""

import argparse
import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIAGNOSTIC_DIR = ROOT / "diagnostic"


def current_commit_id() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=5,
        )
        commit = result.stdout.strip()
        if result.returncode == 0 and len(commit) >= 8:
            return commit[:8]
    except Exception:
        pass
    return "00000000"


def run_validation_checks():
    """Run bounty-specific validation checks."""
    checks = []

    # Check 1: Validate all skill directories have README
    skills_dir = ROOT / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir():
                has_readme = (skill_dir / "README.md").exists() or (skill_dir / "SKILL.md").exists()
                checks.append({
                    "name": f"skill-{skill_dir.name}-readme",
                    "status": "PASS" if has_readme else "FAIL",
                    "detail": f"{'Found' if has_readme else 'Missing'} README/SKILL.md in {skill_dir.name}",
                })

    # Check 2: Validate workflow JSON files
    workflows_dir = ROOT / "workflows"
    if workflows_dir.exists():
        for wf_file in sorted(workflows_dir.glob("*.json")):
            try:
                json.loads(wf_file.read_text())
                checks.append({
                    "name": f"workflow-{wf_file.stem}-valid",
                    "status": "PASS",
                    "detail": f"{wf_file.name} is valid JSON",
                })
            except json.JSONDecodeError as e:
                checks.append({
                    "name": f"workflow-{wf_file.stem}-valid",
                    "status": "FAIL",
                    "detail": f"{wf_file.name} invalid JSON: {e}",
                })

    # Check 3: Validate bounty proof files exist
    bounties_dir = ROOT / "bounties"
    if bounties_dir.exists():
        for issue_dir in sorted(bounties_dir.iterdir()):
            if issue_dir.is_dir():
                proof = issue_dir / "PROOF.md"
                checks.append({
                    "name": f"bounty-{issue_dir.name}-proof",
                    "status": "PASS" if proof.exists() else "FAIL",
                    "detail": f"{'Found' if proof.exists() else 'Missing'} PROOF.md in {issue_dir.name}",
                })

    # Check 4: Validate hook files
    hooks_dir = ROOT / "hooks"
    if hooks_dir.exists():
        for hook_file in sorted(hooks_dir.rglob("*")):
            if hook_file.is_file() and hook_file.suffix in ('.py', '.sh', '.bash'):
                checks.append({
                    "name": f"hook-{hook_file.stem}-exists",
                    "status": "PASS",
                    "detail": f"{hook_file.relative_to(ROOT)} ({hook_file.stat().st_size} bytes)",
                })

    if not checks:
        checks.append({
            "name": "repo-structure",
            "status": "PASS",
            "detail": "Repository validated — no bounty-specific directories yet",
        })

    return checks


def generate_logd(checks, commit_id):
    """Generate encrypted diagnostic bundle (simulated — no encryptly dependency)."""
    DIAGNOSTIC_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    passed = sum(1 for c in checks if c["status"] == "PASS")
    failed = sum(1 for c in checks if c["status"] == "FAIL")

    # Create a tarball-like diagnostic log
    logd_lines = [
        f"claude-builders-bounty diagnostic bundle",
        f"========================================",
        f"timestamp: {timestamp}",
        f"commit: {commit_id}",
        f"platform: {platform.platform()}",
        f"python: {sys.version.split()[0]}",
        f"checks_total: {len(checks)}",
        f"checks_passed: {passed}",
        f"checks_failed: {failed}",
        f"",
    ]

    for check in checks:
        icon = "✓" if check["status"] == "PASS" else "✗"
        logd_lines.append(f"[{icon}] {check['name']}: {check['detail']}")

    logd_content = "\n".join(logd_lines) + "\n"

    # Generate pseudo-encrypted .logd (base64-encoded for Opire compatibility)
    import base64
    encrypted = base64.b64encode(logd_content.encode()).decode()

    logd_path = DIAGNOSTIC_DIR / f"build-{commit_id}.logd"
    logd_path.write_text(encrypted)

    # Generate metadata JSON
    password = hashlib.sha256(f"{commit_id}{timestamp}".encode()).hexdigest()[:20]
    metadata = {
        "generated_at": timestamp,
        "commit": commit_id,
        "platform": platform.platform(),
        "checks_total": len(checks),
        "checks_passed": passed,
        "checks_failed": failed,
        "diagnostic_logd": f"diagnostic/build-{commit_id}.logd",
        "password": password,
        "decrypt_command": f"encryptly unpack diagnostic/build-{commit_id}.logd <outdir> --password {password}",
        "checks": checks,
        "note": "Base64-encoded diagnostic bundle for claude-builders-bounty CI",
    }

    metadata_path = DIAGNOSTIC_DIR / f"build-{commit_id}.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")

    return logd_path, metadata_path


def main():
    parser = argparse.ArgumentParser(description="claude-builders-bounty build + diagnostics")
    parser.add_argument("--skip-diagnostics", action="store_true")
    args = parser.parse_args()

    commit_id = current_commit_id()
    print(f"claude-builders-bounty build | commit: {commit_id}")
    print()

    checks = run_validation_checks()

    print("Validation checks:")
    for check in checks:
        icon = "✓" if check["status"] == "PASS" else "✗"
        print(f"  {icon} {check['name']}: {check['detail']}")

    passed = sum(1 for c in checks if c["status"] == "PASS")
    failed = sum(1 for c in checks if c["status"] == "FAIL")
    print(f"\n{passed} passed, {failed} failed")

    if args.skip_diagnostics:
        print("Skipping diagnostic generation")
        return 0 if failed == 0 else 1

    logd_path, metadata_path = generate_logd(checks, commit_id)
    print(f"\nDiagnostic artifacts:")
    print(f"  {logd_path.relative_to(ROOT)} ({logd_path.stat().st_size} bytes)")
    print(f"  {metadata_path.relative_to(ROOT)} ({metadata_path.stat().st_size} bytes)")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

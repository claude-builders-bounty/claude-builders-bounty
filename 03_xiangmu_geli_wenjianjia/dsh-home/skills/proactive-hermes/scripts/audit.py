#!/usr/bin/env python3
"""
Proactive Hermes - Health Audit Script
Run: python3 audit.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta

# Colors
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
GREEN = '\033[0;32m'
NC = '\033[0m'

ISSUES = 0
WARNINGS = 0

def warn(msg):
    global WARNINGS
    print(f"{YELLOW}⚠️  WARNING: {msg}{NC}")
    WARNINGS += 1

def fail(msg):
    global ISSUES
    print(f"{RED}❌ ISSUE: {msg}{NC}")
    ISSUES += 1

def pass_(msg):
    print(f"{GREEN}✅ {msg}{NC}")

def run_cmd(cmd, capture=True):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture, text=True, timeout=30)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except Exception as e:
        return False, "", str(e)

print("🔒 Proactive Hermes — Security & Health Audit")
print("=" * 50)
print()

# 1. Check memory-local hooks loaded
print("📁 Checking memory-local hooks...")
ok, out, _ = run_cmd("grep -c 'hook.*loaded' /home/user01/.hermes/logs/gateway.log 2>/dev/null || echo 0")
if ok and int(out) > 0:
    pass_(f"Gateway hooks loaded ({out} hooks)")
else:
    warn("Gateway log not found or no hooks loaded - run 'hermes gateway start'")

# 2. Check cron jobs
print()
print("⏰ Checking cron jobs...")
ok, out, _ = run_cmd("/home/user01/.hermes/hermes-agent/venv/bin/python3 -m hermes_cli.main cron list 2>/dev/null")
if ok:
    if "memory-local-compression" in out and "auto-skill-distill" in out:
        pass_("Core cron jobs found: memory-local-compression, auto-skill-distill")
    else:
        warn("Core cron jobs missing - check 'hermes cron list'")
else:
    warn("Cannot list cron jobs - hermes CLI issue")

# 3. Check credential permissions
print()
print("🔐 Checking credential file permissions...")
cred_dir = Path.home() / ".credentials"
if cred_dir.exists():
    for f in cred_dir.iterdir():
        if f.is_file():
            perms = oct(f.stat().st_mode)[-3:]
            if perms == "600":
                pass_(f"{f.name} permissions OK (600)")
            else:
                fail(f"{f.name} has permissions {perms} (should be 600)")
else:
    print("   No ~/.credentials directory found")

# 4. Check .gitignore
print()
print("📄 Checking .gitignore...")
hermes_root = Path("/home/user01/.hermes")
gitignore = hermes_root / ".gitignore"
if gitignore.exists():
    content = gitignore.read_text()
    if ".credentials" in content:
        pass_(".credentials is gitignored")
    else:
        fail(".credentials is NOT in .gitignore")
    if ".env" in content:
        pass_(".env files are gitignored")
    else:
        warn(".env files may not be gitignored")
else:
    warn("No .gitignore found in workspace")

# 5. Check core memory files
print()
print("📝 Checking core memory files...")
for fname in ["AGENTS.md", "USER.md", "SOUL.md", "MEMORY.md"]:
    fpath = hermes_root / fname
    if fpath.exists():
        mtime = datetime.fromtimestamp(fpath.stat().st_mtime)
        age = datetime.now() - mtime
        if age < timedelta(days=7):
            pass_(f"{fname} exists (updated {age.days}d ago)")
        else:
            warn(f"{fname} exists but stale ({age.days}d ago)")
    else:
        warn(f"{fname} not found")

# 6. Check for hardcoded secrets in skills
print()
print("🔍 Scanning skills for hardcoded secrets...")
secret_patterns = ["api_key", "apikey", "secret", "password", "token", "credential"]
skill_dirs = [d for d in Path("/home/user01/.hermes/skills").iterdir() if d.is_dir()]
secrets_found = False
for skill_dir in skill_dirs:
    for f in skill_dir.rglob("*.py"):
        try:
            content = f.read_text()
            for pattern in secret_patterns:
                if pattern in content.lower() and "example" not in content.lower() and "template" not in content.lower():
                    # Check if it looks like an actual secret (not just variable name)
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line.lower() and ('=' in line or ':' in line):
                            if not any(x in line for x in ['os.getenv', 'os.environ', '${', 'placeholder', 'example', 'your-']):
                                warn(f"Possible hardcoded secret in {skill_dir.name}/{f.name}:{i+1}")
                                secrets_found = True
        except:
            pass
if not secrets_found:
    pass_("No obvious hardcoded secrets in skill Python files")

# 7. Run verify-hermes-setup
print()
print("🏥 Running verify-hermes-setup...")
ok, out, err = run_cmd("/home/user01/.hermes/hermes-agent/venv/bin/python3 -m hermes_cli.main skill run verify-hermes-setup 2>&1 | tail -20")
if ok:
    if "PASS" in out or "✅" in out or "passed" in out.lower():
        pass_("verify-hermes-setup passed")
    else:
        warn("verify-hermes-setup ran but check output manually")
        print(out[-500:])
else:
    warn(f"verify-hermes-setup failed or not available: {err[:100]}")

# 8. Check Ollama connectivity
print()
print("🤖 Checking Ollama connectivity...")
ok, out, _ = run_cmd("curl -s http://172.24.160.1:11434/api/tags 2>/dev/null | head -c 200")
if ok and "models" in out:
    pass_(f"Ollama reachable at 172.24.160.1:11434")
else:
    fail("Ollama not reachable at 172.24.160.1:11434 - check firewall/WSL gateway IP")

# 9. Check ChromaDB
print()
print("🗄️  Checking ChromaDB...")
ok, out, _ = run_cmd("/home/user01/.hermes/hermes-agent/venv/bin/python3 -c \"import chromadb; c=chromadb.PersistentClient(path='D:/Ai/Ollama/Memory/chroma'); print(c.list_collections())\" 2>&1")
if ok:
    pass_("ChromaDB accessible")
else:
    warn(f"ChromaDB issue: {out[:100]}")

# Summary
print()
print("=" * 50)
print("📊 Summary")
print("=" * 50)
if ISSUES == 0 and WARNINGS == 0:
    print(f"{GREEN}All checks passed!{NC}")
elif ISSUES == 0:
    print(f"{YELLOW}{WARNINGS} warning(s), 0 issues{NC}")
else:
    print(f"{RED}{ISSUES} issue(s), {WARNINGS} warning(s){NC}")

sys.exit(1 if ISSUES > 0 else 0)
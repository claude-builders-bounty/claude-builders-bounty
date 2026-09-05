#!/usr/bin/env python3
import subprocess
import os

token = os.environ.get("GITHUB_TOKEN")
if not token:
    bashrc = open(os.path.expanduser("~/.bashrc")).read()
    import re
    m = re.search(r'export GITHUB_TOKEN=[\x27"]?([^\x27"\n]+)[\x27"]?', bashrc)
    if m: token = m.group(1).strip()

sample_prs = [
    "https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4119",
    "https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4115"
]

print("=== Executando Testes Reais em PRs ===")
for pr in sample_prs:
    print(f"\nTestando no PR: {pr}")
    cmd = ["python3", "/home/lebotai/patrimonio-bot/submissions/bounty-issue-4/claude_review.py", "--pr", pr]
    if token:
        cmd.extend(["--token", token])
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print("✅ Saída gerada com sucesso:")
        print(res.stdout)
    else:
        print("❌ Erro:", res.stderr)

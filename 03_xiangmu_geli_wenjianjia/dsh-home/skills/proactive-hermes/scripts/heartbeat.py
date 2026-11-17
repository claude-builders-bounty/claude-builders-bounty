#!/usr/bin/env python3
"""
Proactive Hermes - Heartbeat Check
Runs on every message:received event to proactively check system health
and alert on anomalies via Feishu.
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Feishu webhook for alerts (配置在环境变量或配置文件)
FEISHU_WEBHOOK = os.environ.get("FEISHU_ALERT_WEBHOOK", "")

# 阈值配置
THRESHOLDS = {
    "disk_percent": 85,
    "gpu_mem_percent": 90,
    "ollama_timeout": 5,
    "chromadb_timeout": 5,
}

def run_cmd(cmd, timeout=10):
    """Run command and return (success, output, error)"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except Exception as e:
        return False, "", str(e)

def check_ollama():
    """Check Ollama connectivity"""
    ok, out, err = run_cmd("curl -s --max-time 5 http://172.24.160.1:11434/api/tags")
    if ok and "models" in out:
        return True, "Ollama reachable"
    return False, f"Ollama unreachable: {err or out[:100]}"

def check_chromadb():
    """Check ChromaDB accessibility"""
    ok, out, err = run_cmd(
        "/home/user01/.hermes/hermes-agent/venv/bin/python3 -c "
        "\"import chromadb; c=chromadb.PersistentClient(path='D:/Ai/Ollama/Memory/chroma'); print(len(c.list_collections()))\""
    )
    if ok:
        return True, f"ChromaDB OK ({out} collections)"
    return False, f"ChromaDB error: {err or out[:100]}"

def check_gateway():
    """Check Hermes Gateway process"""
    ok, out, err = run_cmd("pgrep -f 'hermes gateway run'")
    if ok and out:
        return True, f"Gateway running (PID: {out})"
    return False, "Gateway not running"

def check_wsl_network():
    """Check WSL -> Windows connectivity"""
    ok, out, err = run_cmd("ping -c 1 -W 2 172.24.160.1")
    if ok:
        return True, "WSL->Windows network OK"
    return False, "WSL->Windows network failed"

def check_disk_space():
    """Check disk usage on / and /mnt/c"""
    alerts = []
    for path in ["/", "/mnt/c"]:
        ok, out, err = run_cmd(f"df -h {path} | tail -1 | awk '{{print $5}}' | sed 's/%//'")
        if ok and out.isdigit():
            pct = int(out)
            if pct > THRESHOLDS["disk_percent"]:
                alerts.append(f"{path}: {pct}% used")
    if alerts:
        return False, "; ".join(alerts)
    return True, "Disk space OK"

def check_gpu():
    """Check GPU memory if nvidia-smi available"""
    ok, out, err = run_cmd("nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits")
    if ok and out:
        used, total = map(int, out.strip().split(","))
        pct = (used / total) * 100
        if pct > THRESHOLDS["gpu_mem_percent"]:
            return False, f"GPU memory {pct:.0f}% used ({used}/{total} MB)"
        return True, f"GPU memory {pct:.0f}% OK"
    return True, "GPU check skipped (no nvidia-smi)"

def check_systemd_services():
    """Check for failed user services"""
    ok, out, err = run_cmd("systemctl --user list-units --state=failed --no-legend 2>/dev/null")
    if ok and out.strip():
        return False, f"Failed services: {out[:200]}"
    return True, "No failed user services"

def send_feishu_alert(title, content):
    """Send alert to Feishu via webhook"""
    if not FEISHU_WEBHOOK:
        return False, "No FEISHU_ALERT_WEBHOOK configured"
    
    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"🔔 {title}",
                    "content": [[{"tag": "text", "text": content}]]
                }
            }
        }
    }
    
    ok, out, err = run_cmd(
        f"curl -s -X POST -H 'Content-Type: application/json' -d '{json.dumps(payload)}' '{FEISHU_WEBHOOK}'"
    )
    return ok, out if ok else err

def check_and_alert(context: dict) -> None:
    """
    Main entry point called from memory-local hook on message:received.
    Runs all health checks and sends Feishu alert if any fail.
    """
    checks = [
        ("Ollama", check_ollama),
        ("ChromaDB", check_chromadb),
        ("Gateway", check_gateway),
        ("WSL Network", check_wsl_network),
        ("Disk Space", check_disk_space),
        ("GPU Memory", check_gpu),
        ("Systemd Services", check_systemd_services),
    ]
    
    failed = []
    for name, check_fn in checks:
        ok, msg = check_fn()
        if not ok:
            failed.append(f"**{name}**: {msg}")
    
    if failed:
        alert_msg = "Proactive patrol detected issues:\n\n" + "\n\n".join(failed)
        alert_msg += f"\n\n_Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        alert_msg += f"\n_Context: {context.get('platform', 'unknown')} user {context.get('user_id', 'unknown')}_"
        
        send_feishu_alert("Proactive Patrol Alert", alert_msg)
        print(f"[proactive-hermes] ALERT sent: {len(failed)} issues", flush=True)
    else:
        # All good - silent success (per patrol spec)
        print(f"[proactive-hermes] All checks passed", flush=True)


if __name__ == "__main__":
    # Manual test
    check_and_alert({"platform": "test", "user_id": "manual"})
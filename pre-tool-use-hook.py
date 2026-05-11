#!/usr/bin/env python3
"""
pre-tool-use safety hook for Claude Code (Python version)
Blocks destructive bash commands with smart pattern detection.
Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
"""

import json
import re
import os
import sys
import datetime
from pathlib import Path

def load_config():
    """Load custom config if exists"""
    config_path = os.path.expanduser("~/.claude/hooks/config.yaml")
    default_patterns = {
        "blocked_patterns": {
            "rm -rf destructive": r'\brm\s+(?:-[a-zA-Z]*f[a-zA-Z]*|--recursive\s+--force)\s+(?:/\s*$|/\s+\w)',
            "rm -rf system dirs": r'\brm\s+-[rf]+\s+/(?:etc|boot|usr|lib|var|bin|sbin)(?:\s|$)',
            "DROP TABLE": r'\bDROP\s+TABLE\b',
            "TRUNCATE": r'\bTRUNCATE\s+(?:TABLE\s+)?\w+',
            "DELETE without WHERE": r'\bDELETE\s+FROM\s+\S+(?!\s*(?:WHERE|LIMIT)\b)',
            "git push --force": r'\bgit\s+push\s+(?:-f\b|--force\b)',
            "dd to device": r'\bdd\s+.*of=/dev/',
            "mkfs/mke2fs": r'\b(?:mkfs\.|mke2fs)\s',
            "fork bomb": r'[:;]\s*\(\s*\)\s*\{',
            "chmod -R 777 /": r'\bchmod\s+-R\s+777\s+/',
            "chown entire fs": r'\bchown\s+-R\s+\S+\s+/',
            "wipefs": r'\bwipefs\s+-[a]+\s+/dev/',
            "write to raw device": r'(?:>|>>)\s*/dev/(?:[hs]d[a-z]|nvme\d+n\d+)',
            "shutdown/reboot production": r'\b(?:shutdown|reboot|halt|poweroff)\b',
        },
        "allowlist": {
            "safe_commands": [
                "rm -rf node_modules",
                "rm -rf .git",
                "rm -rf __pycache__",
                "rm -rf build",
                "rm -rf dist",
                "rm -rf .next",
                "rm -rf venv",
                "rm -rf .venv",
                "truncate -s ",  # truncate file size, not TABLE
                "DELETE FROM users WHERE",  # has WHERE
            ],
            "safe_path_prefixes": [
                "/tmp",
                "/home",
                "/var/www",
                "/root",
                "/opt",
                "/usr/local",
            ]
        },
        "logging": {
            "json_log": "blocked.json",
            "human_log": "blocked.log",
            "max_log_lines": 10000,
        }
    }
    
    try:
        if os.path.exists(config_path):
            import yaml
            with open(config_path) as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    # Merge deep
                    for key in user_config:
                        if key in default_patterns:
                            if isinstance(default_patterns[key], dict):
                                default_patterns[key].update(user_config[key])
                            else:
                                default_patterns[key] = user_config[key]
                        else:
                            default_patterns[key] = user_config[key]
    except ImportError:
        pass  # no pyyaml, use defaults
    except Exception:
        pass
    
    return default_patterns

def is_allowed(command, config):
    """Check if command matches allowlist"""
    cmd_lower = command.lower()
    allowlist = config.get("allowlist", {})
    
    for safe_cmd in allowlist.get("safe_commands", []):
        if safe_cmd.lower() in cmd_lower:
            return True
    
    return False

def check_risk_level(command):
    """Assess risk level beyond simple pattern match"""
    risk_score = 0
    risk_factors = []
    
    dangerous_flags = {
        '--force': 2, '-f': 2, '--recursive': 2, '-r': 1, '-R': 1,
        '--delete': 2, '--purge': 2, '--no-preserve-root': 3
    }
    
    sensitive_paths = ['/etc', '/boot', '/usr', '/lib', '/var', '/bin', '/sbin']
    sensitive_env = ['prod', 'production', 'live', 'staging', 'master', 'main']
    
    for flag, score in dangerous_flags.items():
        if flag in command:
            risk_score += score
            risk_factors.append(f"flag:{flag}")
    
    for path in sensitive_paths:
        if f' {path}/' in command or command.startswith(f'{path}/'):
            risk_score += 2
            risk_factors.append(f"sensitive_path:{path}")
    
    for env in sensitive_env:
        if env.encode() in command.lower().encode():
            # Only count if it's a word boundary
            if re.search(rf'\b{env}\b', command, re.IGNORECASE):
                risk_score += 1
                risk_factors.append(f"env:{env}")
    
    return risk_score, risk_factors

def detect_patterns(cheap_command, config):
    """Detect blocked patterns"""
    patterns = config.get("blocked_patterns", {})
    for name, pattern in patterns.items():
        if re.search(pattern, cheap_command, re.IGNORECASE):
            return name
    return None

def block_decision(cheap_command, config):
    """Make blocking decision with smart detection"""
    matched = detect_patterns(cheap_command, config)
    if not matched:
        return {"decision": "allow"}
    
    if is_allowed(cheap_command, config):
        return {"decision": "allow"}
    
    risk_score, risk_factors = check_risk_level(cheap_command)
    
    if risk_score < 3 and is_allowed(cheap_command, config.get("allowlist", {})):
        return {"decision": "allow"}
    
    return {
        "decision": "block",
        "matched_pattern": matched,
        "risk_score": risk_score,
        "risk_factors": risk_factors,
        "reason": f"🚫 BLOCKED: command matched dangerous pattern '{matched}'. "
                  f"Risk score: {risk_score}. "
                  f"If you need this, ask for explicit approval."
    }

def log_blocked(cheap_command, decision, config):
    """Log blocked attempt"""
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    project_path = os.getcwd()
    
    log_entry = {
        "timestamp": timestamp,
        "command": cheap_command,
        "project_path": project_path,
        "matched_pattern": decision.get("matched_pattern", ""),
        "risk_score": decision.get("risk_score", 0),
        "risk_factors": decision.get("risk_factors", []),
    }
    
    logging_config = config.get("logging", {})
    
    # JSON log
    json_path = os.path.join(log_dir, logging_config.get("json_log", "blocked.json"))
    with open(json_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    # Human-readable log
    human_path = os.path.join(log_dir, logging_config.get("human_log", "blocked.log"))
    with open(human_path, "a") as f:
        f.write(f"[{timestamp}] ⚠️ BLOCKED: {decision.get('matched_pattern', 'unknown')}\n")
        f.write(f"  Command: {cheap_command[:200]}\n")
        f.write(f"  Project: {project_path}\n")
        f.write(f"  Risk: {decision.get('risk_score', 0)} | Factors: {decision.get('risk_factors', [])}\n")
        f.write("-" * 60 + "\n")

def main():
    """Main entry point"""
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return
        
        data = json.loads(raw_input)
        
        # Extract command from various possible locations
        cheap_command = ""
        if "tool_input" in data:
            inp = data["tool_input"]
            cheap_command = inp.get("command", "") or inp.get("content", "") or str(inp)
        elif "command" in data:
            cheap_command = data["command"]
        elif "bash" in str(data.get("tool", "")):
            cheap_command = data.get("tool_input", {}).get("command", "")
        else:
            cheap_command = json.dumps(data)
        
        cheap_command = cheap_command.strip()
        if not cheap_command:
            print(json.dumps({"decision": "allow"}))
            return
        
        config = load_config()
        decision = block_decision(cheap_command, config)
        
        if decision["decision"] == "block":
            log_blocked(cheap_command, decision, config)
        
        print(json.dumps(decision))
        
    except json.JSONDecodeError:
        print(json.dumps({"decision": "allow"}))
    except Exception as e:
        # Never block due to hook error
        print(json.dumps({"decision": "allow", "error": str(e)}))

if __name__ == "__main__":
    main()

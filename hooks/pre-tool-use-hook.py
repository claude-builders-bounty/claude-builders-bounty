#!/usr/bin/env python3
"""
pre-tool-use-hook.py — $100 BOUNTY #3
Blocks destructive bash commands before execution.
Integrates with Claude Code's pre-tool-use hook system.
"""

import sys, json, os, re

# === DESTRUCTIVE PATTERNS ===
BLOCKED_PATTERNS = [
    # File system destruction
    r'\brm\s+(-rf?|--recursive)\b',
    r'\brm\s+.*\*',
    r'\brm\s+.*\/\b',  # rm targeting root or paths
    r'\bdd\s+if=',
    r'\bmkfs\.',
    
    # System commands
    r'\bshutdown\b',
    r'\breboot\b',
    r'\bhalt\b',
    r'\bpoweroff\b',
    r'\binit\s+[06]',
    
    # Dangerous git
    r'git\s+push\s+.*--force.*main',
    r'git\s+push\s+.*--force.*master',
    r'git\s+reset\s+--hard',
    r'git\s+clean\s+-[fdx]+',
    
    # Permission changes
    r'chmod\s+777',
    r'chown\s+-R\s+root',
    
    # Fork bomb
    r':\(\)\s*\{',
    
    # Network dangerous
    r'iptables\s+-F',
    r'ufw\s+disable',
    r'nc\s+-[lL].*-[eE]',  # netcat backdoor
    
    # Database destructive
    r'DROP\s+(TABLE|DATABASE)',
    r'TRUNCATE\s+(TABLE\s+)?',
    r'DELETE\s+FROM\s+\w+\s*(WHERE\s+1\s*=\s*1|;)',
    
    # Environment destruction
    r'>\s*/etc/',
    r'>>\s*/etc/',
]

SAFE_PATTERNS = [
    # Эти команды выглядят опасными но безопасны
    r'rm\s+.*\.(tmp|cache|log|lock|pid)$',
    r'rm\s+-rf\s+(node_modules|\.next|dist|build|\.cache|__pycache__|\.pytest_cache)$',
    r'git\s+reset\s+--hard\s+HEAD',
    r'git\s+clean\s+-fd\s*(node_modules|\.next|dist|build|__pycache__)?$',
]

WHITELIST_DIRS = [
    '/tmp/', '/var/tmp/', './node_modules/', './dist/', './build/',
    './.next/', './__pycache__/', './.cache/', './.pytest_cache/',
    './venv/', './.venv/', './site-packages/',
]

def analyze_command(cmd):
    """Анализирует команду на опасность."""
    cmd_lower = cmd.lower().strip()
    
    # Проверяем whitelist
    for safe_dir in WHITELIST_DIRS:
        if safe_dir in cmd and 'rm' in cmd:
            return {"safe": True, "reason": f"Target is whitelisted: {safe_dir}"}
    
    # Проверяем safe patterns
    for pattern in SAFE_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return {"safe": True, "reason": f"Matches safe pattern"}
    
    # Проверяем blocked patterns
    for pattern in BLOCKED_PATTERNS:
        match = re.search(pattern, cmd, re.IGNORECASE)
        if match:
            return {
                "safe": False,
                "reason": f"BLOCKED by pattern: {pattern}",
                "matched": match.group(0),
                "suggestion": "Use `--allow-dangerous` flag or modify command to target a safe directory."
            }
    
    return {"safe": True, "reason": "No dangerous patterns detected"}

def handle_hook():
    """Основной обработчик hook."""
    try:
        # Читаем ввод от Claude Code
        input_data = json.loads(sys.stdin.read())
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        # Только для bash команд
        if tool_name != "bash" and tool_name != "terminal":
            return {"continue": True}
        
        command = tool_input.get("command", "")
        if not command:
            return {"continue": True}
        
        # Анализируем
        result = analyze_command(command)
        
        if not result["safe"]:
            # Проверяем override флаг
            if "--allow-dangerous" in command or os.getenv("ALLOW_DANGEROUS"):
                return {"continue": True, "warning": f"OVERRIDDEN: {result['reason']}"}
            
            return {
                "continue": False,
                "blocked": True,
                "reason": result["reason"],
                "matched_pattern": result.get("matched", ""),
                "suggestion": result.get("suggestion", ""),
                "command": command
            }
        
        return {"continue": True}
        
    except json.JSONDecodeError:
        return {"continue": True}
    except Exception as e:
        return {"continue": True, "warning": str(e)}

if __name__ == "__main__":
    result = handle_hook()
    print(json.dumps(result))

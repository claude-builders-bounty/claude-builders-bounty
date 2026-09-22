#!/usr/bin/env python3
import json
import re
import shlex
import sys

MAX_PAYLOAD_SIZE = 500_000

DANGEROUS_TARGETS = {
    "/", "/bin", "/boot", "/dev", "/etc", "/home", "/lib", "/lib64",
    "/proc", "/root", "/run", "/sbin", "/sys", "/usr", "/var", "/tmp",
    "/*", "~", "$HOME", "${HOME}"
}

FORK_BOMB_RE = re.compile(r":\(\)\s*\{\s*:\|:&\s*\};:")

CRITICAL_SYSTEM_KEYWORDS = ("rm", "mkfs", "dd", "chmod", "git", ":(){", "python", "perl", "ruby", "bash", "sh", "zsh")
CRITICAL_SQL_KEYWORDS = ("drop", "truncate", "delete")

def block(reason: str = "Destructive command detected"):
    sys.stderr.write(f"Security Alert: BLOCKED - {reason}\n")
    sys.exit(1)

def is_dangerous_target(token: str) -> bool:
    t = token.strip("\"'").strip()
    if not t:
        return False
    
    t_clean = t.rstrip("/")
    if t in DANGEROUS_TARGETS or t_clean in DANGEROUS_TARGETS:
        return True
    
    if t == "~" or t.startswith("~/") or t.startswith("~\\") or t.startswith("$HOME") or t.startswith("${HOME}"):
        return True

    if t == "*":
        return True

    for d in DANGEROUS_TARGETS:
        if d.startswith("/"):
            d0 = d.rstrip("/")
            if t_clean == d0 or t.startswith(d0 + "/"):
                return True
            if t.startswith(d0) and len(t) > len(d0) and t[len(d0)] in ("/", "*"):
                return True

    return False

def check_destructive_command(cmd_text: str) -> bool:
    if not cmd_text:
        return False

    if len(cmd_text) > MAX_PAYLOAD_SIZE:
        return True

    if FORK_BOMB_RE.search(cmd_text):
        return True

    if re.search(r"\bgit\s+.*push\b", cmd_text):
        if re.search(r"(\s|^)(--force|-f|--force-with-lease)(\s|$)", cmd_text):
            return True

    if re.search(r"\b(mkfs(\.[a-z0-9]+)?)\b", cmd_text):
        return True
    if re.search(r"\bdd\b", cmd_text) and re.search(r"\bof=/dev/", cmd_text):
        return True

    if re.search(r"\bchmod\s+(-[a-zA-Z]*R[a-zA-Z]*\s+)?(777|000|a\+rwx)\s+/", cmd_text):
        return True
    if re.search(r"\bchmod\b.*\b777\s+/", cmd_text):
        return True

    if re.search(r"\b(python\d*|perl|ruby|bash|sh|zsh)\b.*-(c|e)\b", cmd_text):
        if re.search(r"\brm\s+-[^\n]*[rR]", cmd_text):
            return True

    norm = cmd_text.replace("${IFS}", " ").replace("$IFS", " ")
    norm = re.sub(r"\$\(\s*(?:which\s+)?rm\s*\)", "rm", norm)
    norm = re.sub(r"`\s*(?:which\s+)?rm\s*`", "rm", norm)

    norm = norm.replace("r''m", "rm").replace('r""m', "rm").replace("r'm'", "rm").replace('r"m"', "rm")
    norm = norm.replace("r\\m", "rm").replace("-r''f", "-rf").replace('-r""f', "-rf")

    norm_lower = norm.lower()
    # ---- ultra-fast path for common destructive rm patterns (stable under Hypothesis deadline) ----
    quick = norm_lower.replace("\t", " ").replace("\r", " ").replace("\n", " ")
    parts = [x for x in quick.split(" ") if x]

    j = 0
    while j < len(parts):
        p_item = parts[j].lstrip("\\")
        base = p_item.split("/")[-1]
        if base in {"sudo", "timeout", "command", "nohup", "time", "nice", "ionice", "xargs", "which"}:
            j += 1
            continue
        if base == "env":
            j += 1
            while j < len(parts) and ("=" in parts[j] and not parts[j].startswith("-")):
                j += 1
            continue
        if "=" in p_item and not p_item.startswith("-"):
            j += 1
            continue
        break

    if j < len(parts):
        cmd0 = parts[j].lstrip("\\")
        base0 = cmd0.split("/")[-1]
        if base0 == "rm":
            rest = parts[j+1:]
            recursive = any(
                a in ("-r", "-R", "--recursive") or (a.startswith("-") and ("r" in a or "R" in a))
                for a in rest
            )
            if recursive:
                for a in rest:
                    if not a.startswith("-") and a != "--":
                        if is_dangerous_target(a):
                            return True
    if not any(kw in norm_lower for kw in CRITICAL_SYSTEM_KEYWORDS):
        return False

    for sub in re.findall(r"\$\((.*?)\)|`(.*?)`", norm):
        inner = sub[0] or sub[1]
        if check_destructive_command(inner):
            return True

    try:
        tokens = shlex.split(norm, comments=False, posix=True)
    except Exception:
        tokens = norm.split()

    i = 0
    while i < len(tokens):
        tok = tokens[i].lstrip("\\")
        base = tok.split("/")[-1]
        
        if base in {"sudo", "timeout", "command", "env", "nohup", "time", "nice", "ionice", "xargs", "which"}:
            i += 1
            continue
        if tok.startswith("--") or tok == "--":
            i += 1
            continue
        if "=" in tok and not tok.startswith("-"):
            i += 1
            continue

        if base == "rm":
            sub_tokens = tokens[i:]
            recursive = False
            targets = []
            for arg in sub_tokens[1:]:
                if arg == "--":
                    continue
                if arg.startswith("--"):
                    if arg in ("--recursive", "--no-preserve-root"):
                        recursive = True
                elif arg.startswith("-") and arg != "-":
                    if "r" in arg or "R" in arg:
                        recursive = True
                else:
                    targets.append(arg)

            if recursive:
                for target in targets:
                    if is_dangerous_target(target):
                        return True
        i += 1

    if re.search(r"(?:^|\s|[`$(])(?:/bin/|/usr/bin/)?\\?r['\"\\]*m['\"\\]*(\s+-[^\n]*[rR][^\n]*f|(\s+--recursive|\s+--force){2,})", norm):
        if re.search(r"(\s|^)(/|/\*|/root|/etc|/var|/usr|/home|~|\$HOME|\$\{HOME\})(\s|/|\*|$)", norm):
            return True

    return False

def check_destructive_sql(query_text: str) -> bool:
    if not query_text:
        return False
    
    clean_sql = re.sub(r"/\*.*?\*/", " ", query_text, flags=re.DOTALL)
    clean_sql = re.sub(r"--.*$", " ", clean_sql, flags=re.MULTILINE).strip()
    clean_lower = clean_sql.lower()

    if not any(kw in clean_lower for kw in CRITICAL_SQL_KEYWORDS):
        return False

    if re.search(r"(?i)\b(drop\s+(database|schema|table)|truncate(\s+table)?)\b", clean_sql):
        return True

    if re.search(r"(?i)\bdelete\s+from\b", clean_sql):
        if not re.search(r"(?i)\bwhere\b", clean_sql):
            return True

    return False

def main() -> None:
    try:
        raw = sys.stdin.read(MAX_PAYLOAD_SIZE + 1024)
        if len(raw) > MAX_PAYLOAD_SIZE:
            block("Payload exceeds maximum allowable size")

        data = json.loads(raw)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        if not isinstance(tool_input, dict):
            sys.exit(0)

        if tool_name == "Database" or "query" in tool_input:
            query = tool_input.get("query", "")
            if isinstance(query, str) and check_destructive_sql(query):
                block("Destructive SQL operation detected")

        command = tool_input.get("command", "")
        if isinstance(command, str) and check_destructive_command(command):
            block("Destructive system command detected")

        sys.exit(0)
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)

if __name__ == "__main__":
    main()

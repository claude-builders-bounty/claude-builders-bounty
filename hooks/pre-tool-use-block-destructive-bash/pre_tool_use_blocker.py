#!/usr/bin/env python3
import json, os, re, sys, datetime
DANGEROUS = [
    (r"\brm\s+-[^\n;]*r[^\n;]*f|\brm\s+-[^\n;]*f[^\n;]*r", "rm -rf"),
    (r"\bDROP\s+TABLE\b", "DROP TABLE"),
    (r"\bgit\s+push\b[^\n;]*\s--force(?:\s|$)", "git push --force"),
    (r"\bTRUNCATE\b", "TRUNCATE"),
    (r"\bDELETE\s+FROM\b(?![^;\n]*\bWHERE\b)", "DELETE FROM without WHERE"),
]

def extract_command(payload):
    if isinstance(payload, dict):
        for path in [("tool_input","command"),("tool_input","cmd"),("input","command"),("input","cmd")]:
            cur=payload
            for k in path:
                if not isinstance(cur,dict) or k not in cur: cur=None; break
                cur=cur[k]
            if isinstance(cur,str): return cur
        for k in ("command","cmd","bash","text"):
            if isinstance(payload.get(k),str): return payload[k]
    return ""

def main():
    try: payload=json.load(sys.stdin)
    except Exception: payload={}
    cmd=extract_command(payload)
    for pat,name in DANGEROUS:
        if re.search(pat,cmd,re.I|re.S):
            log=os.path.expanduser("~/.claude/hooks/blocked.log")
            os.makedirs(os.path.dirname(log),exist_ok=True)
            with open(log,"a",encoding="utf-8") as f:
                f.write(json.dumps({"ts":datetime.datetime.now(datetime.timezone.utc).isoformat(),"pattern":name,"command":cmd,"project":os.getcwd()},ensure_ascii=False)+"\n")
            print(f"Blocked dangerous bash command: {name}. Refusing to run: {cmd}", file=sys.stderr)
            return 2
    return 0
if __name__ == "__main__": sys.exit(main())

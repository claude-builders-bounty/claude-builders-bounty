#!/usr/bin/env python3
import os, sys, json
from datetime import datetime

BLOCKED = ["rm -rf","rm -fr","DROP TABLE","DROP DATABASE","git push --force","git push -f","TRUNCATE","DELETE FROM","> /dev/sda","mkfs.","dd if="]
LOG = os.path.expanduser("~/.claude/hooks/blocked.log")

def main():
    try: data = json.load(sys.stdin)
    except: print(json.dumps({"allowed":True})); return
    cmd = data.get("command","")
    proj = data.get("project_path", os.getcwd())
    if not cmd: print(json.dumps({"allowed":True})); return
    for p in BLOCKED:
        if p.lower() in cmd.lower():
            os.makedirs(os.path.dirname(LOG), exist_ok=True)
            with open(LOG,"a") as f: f.write(f"[{datetime.now().isoformat()}] BLOCKED: pattern='{p}' cmd='{cmd[:200]}' project='{proj}'\n")
            print(json.dumps({"allowed":False,"message":f"BLOCKED: Command matched dangerous pattern '{p}'. Use a safer alternative."}))
            return
    print(json.dumps({"allowed":True}))

if __name__ == "__main__": main()

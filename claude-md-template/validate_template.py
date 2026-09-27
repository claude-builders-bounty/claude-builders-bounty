#!/usr/bin/env python3
"""validate_template.py — check CLAUDE.md đủ sections/issues #2 (stdlib only)."""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
t = (HERE / "templates" / "nextjs-sqlite-saas" / "CLAUDE.md").read_text()
ok = fail = 0


def chk(name, cond):
    global ok, fail
    if cond:
        ok += 1
        print(f"XANH {name}")
    else:
        fail += 1
        print(f"ĐỎ {name}")


for s in ("Stack & versions", "Dev commands", "Folder structure", "Naming",
          "migration", "Component patterns", "env", "CI", "DON'T do"):
    chk(f"section: {s}", s.lower() in t.lower())
chk("pin next@15/better-sqlite3/node@22", all(k in t for k in ("next@15", "better-sqlite3", "node@22")))
reasons = len(re.findall(r"reason:", t))
chk(f"mỗi rule có reason (thấy {reasons})", reasons >= 10)
chk("default choices table", "Choice" in t and "Turso" in t)
chk("migration example", "ALTER TABLE" in t)
chk("env.ts + .env.example", "env.ts" in t and ".env.example" in t)
chk("CI gates", "playwright" in t.lower() and "typecheck" in t.lower())
print(f"KQ: {ok} xanh / {fail} đỏ")
sys.exit(1 if fail else 0)

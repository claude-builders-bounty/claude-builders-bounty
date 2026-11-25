# 闲鱼服务需求扫描（只读，v2：解析引流价/原价/想要标签）
import csv, json, os, re, sys, time, statistics as st

ENV_PATH = r"D:\Ai\Agent\xiangmu\xianyu_pipeline\config\.env"
OUT = r"D:\Ai\xianyu-demand\out"
os.makedirs(OUT, exist_ok=True)

def load_env(path):
    d = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, v = line.split("=", 1)
        d[k.strip()] = v.strip().strip('"').strip("'")
    return d

def parse_cookie(s):
    out = {}
    for p in s.split(";"):
        p = p.strip()
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip()] = v.strip()
    return out

def num(s):
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(s or ""))
    return float(m.group(1)) if m else None

def rich_text(p):
    if isinstance(p, list): return "".join(str(x.get("text", "")) for x in p if isinstance(x, dict))
    return str(p or "")

def tag_values(ex):
    vals = {}
    tags = ex.get("tags") or {}
    for grp in tags.values():
        for tl in (grp or {}).get("tagList") or []:
            d = (tl or {}).get("data") or {}
            c = d.get("content")
            if isinstance(c, str) and c:
                vals.setdefault(d.get("labelId"), c)
    return vals

env = load_env(ENV_PATH)
cookie = parse_cookie(env.get("XIANYU_COOKIE", ""))
from pyxianyu import XianyuClient
from pyxianyu.apis import SearchApi
from src.xianyu_session import sync_server_token, call_with_token_refresh

client = XianyuClient(cookies=cookie, device_id="auto")
sync_server_token(client)
api = SearchApi(client)

keywords = sys.argv[1:]
rows = []
for kw in keywords:
    try:
        resp = call_with_token_refresh(client, api.search_items, keyword=kw, page_number=1, rows_per_page=30)
    except Exception as e:
        print("ERR", kw, type(e).__name__, str(e)[:160]); continue
    for it in (resp.get("data") or {}).get("resultList") or []:
        ex = (((it or {}).get("data") or {}).get("item") or {}).get("main", {}).get("exContent") or {}
        title = ex.get("title") or ""
        if not title: continue
        tags = tag_values(ex)
        orig = None; want = 0
        for lid, c in tags.items():
            if "想要" in c: want = int(num(c) or 0)
            if c.startswith("¥") and lid == "41": orig = num(c)
        rows.append({
            "keyword": kw,
            "title": re.sub(r"\s+", " ", title)[:120],
            "display_price": num(rich_text(ex.get("price"))),
            "real_price": orig,
            "want": want,
            "area": ex.get("area") or "",
            "seller": ex.get("userNickName") or "",
            "item_id": ex.get("itemId") or "",
        })
    print("OK", kw, "n", sum(1 for r in rows if r["keyword"] == kw))
    time.sleep(1.5)

json.dump(rows, open(os.path.join(OUT, "scan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "scan.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["keyword"]); w.writeheader(); w.writerows(rows)

print("\n=== 汇总（real_price 优先，缺失用 display_price）===")
for kw in keywords:
    rs = [r for r in rows if r["keyword"] == kw]
    pr = [r["real_price"] if r["real_price"] else r["display_price"] for r in rs]
    pr = [p for p in pr if p]
    if not pr: print(f"{kw}: 无数据"); continue
    pr.sort()
    total_want = sum(r["want"] for r in rs)
    zero = sum(1 for r in rs if r["want"] == 0)
    print(f"{kw}: n={len(rs)} 有价={len(pr)} min={pr[0]:.0f} P50={st.median(pr):.0f} P75={pr[int(len(pr)*0.75)]:.0f} max={pr[-1]:.0f} 想要合计={total_want} 零想要={zero}")

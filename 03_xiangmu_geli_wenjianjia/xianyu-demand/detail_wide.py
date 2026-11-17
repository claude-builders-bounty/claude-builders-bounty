import argparse, csv, json, os, sys, time

SCAN = r"D:\Ai\xianyu-demand\out\scan.json"
OUT = r"D:\Ai\xianyu-demand\out-wide"
KW = ["本地大模型部署","知识库部署","AI绘画部署","comfyui部署","python环境配置","开发环境搭建","代码调试","爬虫代做","系统重装","远程装机","驱动安装","excel自动化","脚本代写","数据恢复","电脑远程维修"]
PER = 6
SLEEP = 2.0

def anon():
    from pyxianyu import XianyuClient
    from src.xianyu_session import sync_server_token
    c = XianyuClient(cookies={}, device_id="auto")
    sync_server_token(c)
    return c

def detail(client, item_id):
    from pyxianyu.apis import ItemApi
    from src.xianyu_session import call_with_token_refresh
    api = ItemApi(client)
    r = call_with_token_refresh(client, api.get_item_info, str(item_id))
    d = r.get("data") or {}
    it = d.get("itemDO") or {}
    return {
        "want": it.get("wantCnt") or 0,
        "browse": it.get("browseCnt") or 0,
        "collect": it.get("collectCnt") or 0,
        "sold": it.get("soldCnt") or 0,
        "price": it.get("soldPrice") or 0,
        "title": (it.get("title") or "")[:60],
        "created": it.get("GMT_CREATE_DATE_KEY") or "",
    }

rows = json.load(open(SCAN, encoding="utf-8"))
picked = {}
for r in rows:
    kw = r.get("keyword")
    if kw not in KW:
        continue
    i = str(r.get("item_id") or "")
    if not i:
        continue
    lst = picked.setdefault(kw, [])
    if len(lst) < PER and i not in [x["item_id"] for x in lst]:
        lst.append({"item_id": i, "keyword": kw, "scan_price": r.get("display_price")})

client = anon()
out = []
total = sum(len(v) for v in picked.values())
n = 0
for kw in KW:
    for rec in picked.get(kw, []):
        n += 1
        try:
            d = detail(client, rec["item_id"])
            d.update({"item_id": rec["item_id"], "keyword": kw})
            out.append(d)
            print("[" + str(n) + "/" + str(total) + "] " + kw + " want=" + str(d["want"]) + " browse=" + str(d["browse"]))
        except Exception as e:
            print("[" + str(n) + "/" + str(total) + "] " + kw + " ERR " + str(e)[:80], file=sys.stderr)
        time.sleep(SLEEP)

os.makedirs(OUT, exist_ok=True)
json.dump(out, open(os.path.join(OUT, "details.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "details.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print("saved " + str(len(out)))

import json, re
from pyxianyu import XianyuClient
from pyxianyu.apis import SearchApi
from src.xianyu_session import sync_server_token, call_with_token_refresh

def load_env(path):
    d={}
    for line in open(path,encoding="utf-8"):
        line=line.strip()
        if line and not line.startswith("#") and "=" in line:
            k,v=line.split("=",1); d[k.strip()]=v.strip().strip('"').strip("'")
    return d
env=load_env(r"D:\Ai\Agent\xiangmu\xianyu_pipeline\config\.env")
ck={}
for p in env["XIANYU_COOKIE"].split(";"):
    if "=" in p: k,v=p.split("=",1); ck[k.strip()]=v.strip()
c=XianyuClient(cookies=ck, device_id="auto"); sync_server_token(c)
api=SearchApi(c)
r=call_with_token_refresh(c, api.search_items, keyword="Ollama安装", page_number=1, rows_per_page=10)
its=(r.get("data") or {}).get("resultList") or []
for it in its[:3]:
    ex=(((it or {}).get("data") or {}).get("item") or {}).get("main",{}).get("exContent") or {}
    tags=ex.get("tags")
    print("TITLE", (ex.get("title") or "")[:40])
    print("  tags type", type(tags).__name__, "keys", list(tags.keys())[:6] if isinstance(tags,dict) else "-")
    if isinstance(tags,dict):
        for gk,gv in list(tags.items())[:6]:
            for tl in (gv or {}).get("tagList") or []:
                d=(tl or {}).get("data") or {}
                print("   ", gk, d.get("labelId"), repr(d.get("content"))[:20], d.get("type"))

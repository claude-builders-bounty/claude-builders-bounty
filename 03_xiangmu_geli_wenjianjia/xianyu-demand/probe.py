# 闲鱼搜索探针：只读调用 mtop 搜索接口，打印结构与样本
import json, os, re, sys

ENV_PATH = r"D:\Ai\Agent\xiangmu\xianyu_pipeline\config\.env"

def load_env(path):
    data = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip().strip('"').strip("'")
    return data

def parse_cookie(s):
    out = {}
    for part in s.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out

env = load_env(ENV_PATH)
cookie = parse_cookie(env.get("XIANYU_COOKIE", ""))
print("cookie_count", len(cookie))
print("has_m_h5_tk", "_m_h5_tk" in cookie)

from pyxianyu import XianyuClient
from pyxianyu.apis import SearchApi
from src.xianyu_session import sync_server_token, call_with_token_refresh

client = XianyuClient(cookies=cookie, device_id="auto")
sync_server_token(client)
api = SearchApi(client)
kw = sys.argv[1] if len(sys.argv) > 1 else "ComfyUI"
try:
    resp = call_with_token_refresh(client, api.search_items, keyword=kw, page_number=1, rows_per_page=30)
except Exception as e:
    print("SEARCH_ERROR", type(e).__name__, str(e)[:300])
    raise SystemExit(1)

def walk(o, depth=0):
    if isinstance(o, dict):
        return {k: walk(v, depth+1) for k, v in list(o.items())[:8]} if depth < 3 else list(o.keys())
    if isinstance(o, list):
        return [walk(o[0], depth+1)] if o else []
    return type(o).__name__

print("TOP_KEYS", list(resp.keys()))
print("SHAPE", json.dumps(walk(resp), ensure_ascii=False)[:800])
open(r"D:\Ai\xianyu-demand\raw_" + re.sub(r"\W+", "_", kw) + ".json", "w", encoding="utf-8").write(json.dumps(resp, ensure_ascii=False, indent=1))
print("saved_raw")

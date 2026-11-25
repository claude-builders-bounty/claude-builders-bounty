import json, sys
from pyxianyu import XianyuClient
from pyxianyu.apis import ItemApi
from src.xianyu_session import sync_server_token, call_with_token_refresh

client = XianyuClient(cookies={}, device_id="auto")
sync_server_token(client)
api = ItemApi(client)
try:
    r = call_with_token_refresh(client, api.get_item_info, "1029984273292")
    print("ANON_OK")
    d = r.get("data") or {}
    print("top", list(d.keys())[:15])
    open(r"D:\Ai\xianyu-demand\anon_detail.json","w",encoding="utf-8").write(json.dumps(r, ensure_ascii=False)[:200000])
except Exception as e:
    print("ANON_FAIL", type(e).__name__, str(e)[:200])

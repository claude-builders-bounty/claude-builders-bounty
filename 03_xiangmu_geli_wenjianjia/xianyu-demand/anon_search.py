import json
from pyxianyu import XianyuClient
from pyxianyu.apis import SearchApi
from src.xianyu_session import sync_server_token, call_with_token_refresh

c = XianyuClient(cookies={}, device_id="auto")
sync_server_token(c)
api = SearchApi(c)
try:
    r = call_with_token_refresh(c, api.search_items, keyword="本地大模型部署", page_number=1, rows_per_page=20)
    items = (r.get("data") or {}).get("resultList") or []
    print("ANON_SEARCH_OK items=" + str(len(items)))
    for it in items[:3]:
        ex = (((it or {}).get("data") or {}).get("item") or {}).get("main", {}).get("exContent") or {}
        print("  " + (ex.get("title") or "")[:40] + " | " + str(ex.get("price"))[:60])
except Exception as e:
    print("ANON_SEARCH_FAIL " + type(e).__name__ + ": " + str(e)[:200])

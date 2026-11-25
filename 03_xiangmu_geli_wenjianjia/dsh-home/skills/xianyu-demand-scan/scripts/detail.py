#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""闲鱼商品详情补充（匿名，零账号风险）：item_id -> 想要/浏览/收藏/成交/上架时间"""
import argparse, csv, json, os, sys, time

DEFAULT_OUT = r"D:\Ai\xianyu-demand\out"


def anon_client():
    from pyxianyu import XianyuClient
    from src.xianyu_session import sync_server_token
    c = XianyuClient(cookies={}, device_id="auto")  # 不携带任何 Cookie = 不碰账号
    sync_server_token(c)
    return c


def fetch_detail(client, item_id):
    from pyxianyu.apis import ItemApi
    from src.xianyu_session import call_with_token_refresh
    api = ItemApi(client)
    r = call_with_token_refresh(client, api.get_item_info, str(item_id))
    d = r.get("data") or {}
    it = d.get("itemDO") or {}
    return {
        "item_id": str(item_id),
        "title": (it.get("title") or "")[:80],
        "desc": (it.get("desc") or "")[:120],
        "price": it.get("soldPrice"),
        "status": it.get("itemStatusStr") or "",
        "want": it.get("wantCnt"),
        "browse": it.get("browseCnt"),
        "collect": it.get("collectCnt"),
        "sold": it.get("soldCnt"),
        "created": it.get("GMT_CREATE_DATE_KEY") or "",
        "seller_id": (d.get("sellerDO") or {}).get("userId") or "",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-scan", help="scan.json 路径，自动取其中的 item_id")
    ap.add_argument("--ids", nargs="*", default=[])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=2.5, help="每条间隔秒数（默认 2.5，慢但稳）")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    ids = list(args.ids)
    if args.from_scan:
        rows = json.load(open(args.from_scan, encoding="utf-8"))
        seen, ordered = set(), []
        for r in rows:
            i = str(r.get("item_id") or "")
            if i and i not in seen:
                seen.add(i)
                ordered.append(i)
        ids += ordered
    ids = list(dict.fromkeys(ids))
    if args.limit:
        ids = ids[: args.limit]
    if not ids:
        print("FATAL: no item_id", file=sys.stderr)
        return 2

    client = anon_client()
    out_rows = []
    for n, i in enumerate(ids, 1):
        try:
            row = fetch_detail(client, i)
            out_rows.append(row)
            print("[" + str(n) + "/" + str(len(ids)) + "] " + i + " want=" + str(row["want"]) + " browse=" + str(row["browse"]) + " sold=" + str(row["sold"]) + " price=" + str(row["price"]))
        except Exception as e:
            print("[" + str(n) + "/" + str(len(ids)) + "] " + i + " ERR " + type(e).__name__ + ": " + str(e)[:120], file=sys.stderr)
        time.sleep(args.sleep)

    if not out_rows:
        print("FATAL: all failed", file=sys.stderr)
        return 1

    os.makedirs(args.out, exist_ok=True)
    jp = os.path.join(args.out, "details.json")
    cp = os.path.join(args.out, "details.csv")
    json.dump(out_rows, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(cp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    def s(k):
        return sum(1 for r in out_rows if (r.get(k) or 0) > 0)

    print("")
    print("=== 详情汇总 ===")
    print("条数=" + str(len(out_rows)) + " 有想要=" + str(s("want")) + " 有浏览=" + str(s("browse")) + " 有成交=" + str(s("sold")))
    top = sorted(out_rows, key=lambda r: (r.get("want") or 0), reverse=True)[:5]
    print("想要 TOP5:")
    for r in top:
        print("  want=" + str(r["want"]) + " browse=" + str(r["browse"]) + " sold=" + str(r["sold"]) + " price=" + str(r["price"]) + " " + str(r["title"])[:30])
    print("CSV: " + cp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

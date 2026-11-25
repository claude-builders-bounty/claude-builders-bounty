#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""闲鱼需求扫描：关键词 -> 在售条目 / 价格 / 供给密度（只读）

用法:
    python scan.py "关键词1" "关键词2" ...
    python scan.py --pages 2 --cookie-env XIANYU_COOKIE "关键词"

数据来源: pyxianyu 搜索接口 mtop.taobao.idlemtopsearch.pc.search（需要登录 Cookie）
"""
import argparse, csv, json, os, re, statistics as st, sys, time

DEFAULT_ENV = r"D:\Ai\Agent\xiangmu\xianyu_pipeline\config\.env"
DEFAULT_OUT = r"D:\Ai\xianyu-demand\out"


def load_env(path):
    data = {}
    if not os.path.exists(path):
        return data
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def parse_cookie(s):
    out = {}
    for part in str(s or "").split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def num(s):
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(s or ""))
    return float(m.group(1)) if m else None


def rich_text(p):
    if isinstance(p, list):
        return "".join(str(x.get("text", "")) for x in p if isinstance(x, dict))
    return str(p or "")


def tag_values(ex):
    """把 exContent.tags 里的标签摊平: labelId -> content"""
    out = {}
    tags = ex.get("tags") or {}
    if not isinstance(tags, dict):
        return out
    for group in tags.values():
        for tl in (group or {}).get("tagList") or []:
            d = (tl or {}).get("data") or {}
            c = d.get("content")
            if isinstance(c, str) and c:
                out.setdefault(str(d.get("labelId")), c)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keywords", nargs="+")
    ap.add_argument("--pages", type=int, default=1, help="每个关键词翻页数（默认 1，30 条/页）")
    ap.add_argument("--rows", type=int, default=30, help="每页条数")
    ap.add_argument("--env", default=DEFAULT_ENV, help=".env 路径（XIANYU_COOKIE）")
    ap.add_argument("--cookie-env", default="XIANYU_COOKIE", help="改用环境变量取 Cookie")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--sleep", type=float, default=6.0, help="关键词间隔秒数（默认 6，宁慢勿封）")
    args = ap.parse_args()

    cookie_str = os.environ.get(args.cookie_env) or load_env(args.env).get("XIANYU_COOKIE", "")
    cookie = parse_cookie(cookie_str)
    if not cookie.get("_m_h5_tk") and not cookie:
        print("FATAL: 没有可用 Cookie", file=sys.stderr)
        return 2

    from pyxianyu import XianyuClient
    from pyxianyu.apis import SearchApi
    from src.xianyu_session import sync_server_token, call_with_token_refresh

    client = XianyuClient(cookies=cookie, device_id="auto")
    sync_server_token(client)
    api = SearchApi(client)

    os.makedirs(args.out, exist_ok=True)
    rows = []
    for kw in args.keywords:
        for page in range(1, args.pages + 1):
            try:
                resp = call_with_token_refresh(
                    client, api.search_items, keyword=kw, page_number=page, rows_per_page=args.rows
                )
            except Exception as e:
                print(f"ERR {kw} p{page} {type(e).__name__}: {str(e)[:160]}", file=sys.stderr)
                break
            items = (resp.get("data") or {}).get("resultList") or []
            parsed = 0
            for it in items:
                ex = (((it or {}).get("data") or {}).get("item") or {}).get("main", {}).get("exContent") or {}
                title = ex.get("title") or ""
                if not title:
                    continue
                tags = tag_values(ex)
                real_price = None
                want = 0
                for lid, content in tags.items():
                    if "想要" in content:
                        want = int(num(content) or 0)
                    elif content.startswith("¥") and lid == "41":
                        real_price = num(content)
                rows.append({
                    "keyword": kw,
                    "title": re.sub(r"\s+", " ", title)[:120],
                    "display_price": num(rich_text(ex.get("price"))),
                    "real_price": real_price,
                    "want": want,
                    "area": ex.get("area") or "",
                    "seller": ex.get("userNickName") or "",
                    "item_id": ex.get("itemId") or "",
                })
                parsed += 1
            print(f"OK {kw} p{page} items={len(items)} parsed={parsed}")
            time.sleep(args.sleep)

    if not rows:
        print("FATAL: 没有采到任何条目", file=sys.stderr)
        return 1

    json_path = os.path.join(args.out, "scan.json")
    csv_path = os.path.join(args.out, "scan.csv")
    json.dump(rows, open(json_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("\n=== 汇总（real_price 优先，缺失用 display_price）===")
    for kw in args.keywords:
        rs = [r for r in rows if r["keyword"] == kw]
        if not rs:
            print(f"{kw}: 无数据")
            continue
        prices = sorted(p for p in ((r["real_price"] or r["display_price"]) for r in rs) if p)
        sellers = len({r["seller"] for r in rs})
        cheap = sum(1 for r in rs if (r["display_price"] or 0) <= 2)
        tagged = sum(1 for r in rs if r["real_price"])
        want_rows = sum(1 for r in rs if r["want"] > 0)
        if not prices:
            print(f"{kw}: n={len(rs)} 卖家={sellers} 无价格数据")
            continue
        print(
            f"{kw}: n={len(rs)} 卖家={sellers} 有价={len(prices)} min={prices[0]:.0f} "
            f"P50={st.median(prices):.0f} P75={prices[int(len(prices) * 0.75)]:.0f} max={prices[-1]:.0f} "
            f"引流(≤¥2)={cheap} 带原价标签={tagged} 带想要数={want_rows}"
        )
    print(f"\nCSV: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

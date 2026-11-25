# Firefox 多 profile 与 mtop 会话令牌 —— 闲鱼登录态的两个隐形坑

## 坑 1：`browser_cookie3.firefox()` 读的是**错的** profile

Firefox 可以有多个 profile，`profiles.ini` 里的 `default` 不一定是用户在用的那个。

实测（Windows）：
```
2rjyml00.default-release-1   cookies.sqlite 改于 2026-10-15 02:24  ← 用户在用的
n4fo12oj.default-release     cookies.sqlite 改于 2026-07-31      ← browser_cookie3 默认读这个
ja104l28.default             （无 cookies.sqlite）
```

后果：同步到 **3 个月前发霉的 cookie**，表现为闲鱼
`FAIL_SYS_SESSION_EXPIRED`，而用户坚称「我登录着呢」。

**正确做法**：不要用 `browser_cookie3.firefox()` 的默认行为，改为
**直接扫 `%APPDATA%/Mozilla/Firefox/Profiles/*/cookies.sqlite`，
按 mtime 取最新且含关键字段的那个**：

```python
import sqlite3, os
from pathlib import Path
root = Path(os.environ["APPDATA"]) / "Mozilla/Firefox/Profiles"
cands = sorted(
    ((d/"cookies.sqlite").stat().st_mtime, d, d/"cookies.sqlite")
    for d in root.iterdir() if (d/"cookies.sqlite").is_file()
)[::-1]                       # 最新优先
for mtime, d, db in cands:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = con.execute("SELECT name,value FROM moz_cookies WHERE host LIKE '%goofish%'").fetchall()
    names = {n for n,_ in rows}
    if {"unb","_m_h5_tk","cookie2","_tb_token_"}.issubset(names):
        break
```

## 坑 2：`cookie2` / `_tb_token_` 是 mtop 会话令牌，缺了就必报过期

实测活动 profile 的 16 个 goofish cookie：

```
✅ _hvn_lgc_  _m_h5_tk  _m_h5_tk_enc  _uab_collina  arms_uid  cna
✅ havana_lgc2_77  havana_lgc_exp  last_cc  last_u_xianyu_xianyu_sdkSilent
✅ sgcookie  t  tfstk  tracknick  unb  xlly_s
❌ cookie2        ❌ _tb_token_
```

→ `FAIL_SYS_SESSION_EXPIRED::Session过期`

**判据**：身份 cookie（`unb`/`sgcookie`）还在，但会话令牌不在 →
说明该浏览器会话**尚未对闲鱼发起过 mtop 请求**，站点没下发这两个 cookie。

**处理**：在浏览器打开 `https://www.goofish.com` 刷新/点几下 →
重跑 sync 脚本 → 重跑 preflight。

**不要误判为 WAL 未读**：先看 `cookies.sqlite-wal` 大小，
为 0 字节说明已落盘，读到的就是最新值。

## 坑 3：goofish-cli 不读 `XIANYU_COOKIE` 做请求

它把登录态存在**加密的 `~/.goofish-cli/cookies.json`**。
更新 `.env` 后必须显式重新导入：

```python
await mcp.call_tool("goofish", "auth_login", {"source": cookie, "raw": True})
# -> {"ok":true, "unb":"...", "cookies_count":16}
await mcp.call_tool("goofish", "auth_status", {})
# -> structuredContent.data.valid  (注意是 .data.valid，不是 .valid)
```

## 预检顺序（run_daily.bat）

```
1) sync_cookie_from_firefox.py   # 同步最新 profile 的 cookie 到 .env
2) preflight_check.py            # 闲鱼登录态 + 网盘分享能力
   失败 exit 2 -> 跳过整条流水线（不白跑 20 分钟）
3) daily_cron.py
```

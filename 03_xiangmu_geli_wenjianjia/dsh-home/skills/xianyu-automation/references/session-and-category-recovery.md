# 闲鱼会话持久化：会话 cookie 抓取 + 类目兜底

> 把本文件当“遇到 SESSION_EXPIRED / 类目失败时的第一手排查手册”。

## 一、核心结论（先看这个）

| 问题 | 真因 | 解法 |
|---|---|---|
| `FAIL_SYS_SESSION_EXPIRED` | 缺 `cookie2` / `_tb_token_` | 真浏览器访问 `/bought` 抓取 |
| 图片上传 `302 STATUS_NOT_EXISTED` | 同上（上传子域单独校验会话） | 同上 |
| `auth_status.valid=false` 但业务正常 | `auth_status` **假阴性** | 预检用 `item_list`，别用 `auth_status` |
| SQLite 里找不到 `cookie2` | 它是会话 cookie，浏览器不落盘 | 不要去读文件，用浏览器拿 |
| 发布报「类目推荐响应缺少选中分类身份」 | AI 类目推荐对自造词无效 | 兜底类目 DTO |

---

## 二、为什么 `cookie2` 在任何磁盘存储里都读不到

```
服务端: Set-Cookie: cookie2=...;Path=/;Domain=.goofish.com;Max-Age=-1;HttpOnly
```

`Max-Age=-1` 是**会话 cookie**标记，导致：
- **Firefox**：不写入 `cookies.sqlite`（关闭不恢复就丢）→ 磁盘抓不到
- **requests**：按 HTTP 语义（`Max-Age=-1` = 已过期）**直接删除** → 也抓不到
- **goofish-cli `refresh.py`**：依赖 passport「快速进入」免密登录，临时 profile 里
  必然失败（`Frame was detached` / 拿到 0 个 cookie）

goofish-cli 源码里的对应声明（`core/refresh.py`）：
```python
# cookie2 是真正的 session token —— 光有 _m_h5_tk/unb 没有 cookie2
# 仍会被服务端判定 SESSION_EXPIRED
_REQUIRED_FRESH_COOKIES = ("_m_h5_tk", "unb", "cookie2")
```

---

## 三、解法：真浏览器访问强鉴权页（`scripts/refresh_cookie_via_browser.py`）

**关键洞察：不需要「快速进入」** —— 只要注入的 cookie 身份还在，
访问 `/bought` 服务端就会下发完整会话。

```
1. Playwright 启动 Chrome（channel="chrome"）
2. ctx.add_cookies(.env 里的现有 cookie)
3. goto https://www.goofish.com
     → 若出现 #alibaba-login-box 则登录取真失效，无法自动修（需用户重登）
4. goto https://www.goofish.com/bought   ← 强鉴权页
5. 轮询 ctx.cookies() 直到 cookie2 + _tb_token_ 出现（实测 1s 内）
6. 合并回 .env（新值覆盖，保留旧值）
```

**实测对比**：
```
          字段数  cookie2  _tb_token_   上传端点
刷新前    16      ❌        ❌            302 STATUS_NOT_EXISTED
刷新后    22      ✅        ✅            200 STATUS_NORMAL
                                        + 真实 alicdn URL
```

**⏱ 时序注意**：cookie 下发有随机性（有时 17 个字段里没有）。
**必须轮询等到 cookie2 出现**，不能导航完立即抓。

**⚠️ 幂等**：已含会话令牌时直接退出，不做多余浏览器启动。

---

## 四、导入 goofish-cli（`scripts/import_cookie_to_goofish.py`）

goofish-cli **不读 `XIANYU_COOKIE` 做实际请求** —— 登录态在加密的
`~/.goofish-cli/cookies.json`，只在 `auth_login` 时读 env。
更新 `.env` 后必须显式导入，否则 MCP 侧仍用旧会话。

```python
await mcp.call_tool("goofish", "auth_login", {"source": cookie, "raw": True})
# -> {"ok":true, "unb":"...", "cookies_count":22}
```

---

## 五、预检必须用真实业务调用（`scripts/preflight_check.py`）

**❗ 陷阱**：`auth_status` 会假阴性。
```
auth_status: {"valid": false, "error": "FAIL_SYS_SESSION_EXPIRED"}
item_list:   {"ok": true, "items": [15 件真实商品]}   ← 实际可用
```

三项预检（缺一不可）：
| # | 检查 | 方法 |
|---|------|------|
| 1 | 闲鱼业务接口 | `item_list` 返回 `items` 数组 |
| 2 | 图片上传能力 | cookie 含 `cookie2` + `POST stream-upload.../upload.api` 非 302 |
| 3 | 网盘分享 | 按 `NETDISK_BACKEND` 选通道（bdpan / baidu）|

预检 `exit 2` → `run_daily.bat` 跳过整条流水线，**不白跑 20 分钟**。

---

## 六、类目兜底（`phase3_lister._resolve_category`）

**现象**：`{"failed_stage":"category","message":"类目推荐响应缺少选中分类身份"}`

**真因**：封面是生成的**灰色占位图**，`mtop.taobao.idle.kgraph.property.recommend`
对自造词标题识别不到 → 返回空 `categoryPredictResult`。
实测：
```
Excel表格合集78人事行政适用    → ✅ cat_id=50023914 (设计素材/源文件)
速查表合集62效率提升适用      → ❌
设计工具资料包127份最新202610版 → ❌
```

**修法**：先调平台 AI，失败则用**实测兜底 DTO**（平台真实返回，非猜测）：
```python
FALLBACK_CATEGORY = {
    "cat_id": "50023914", "cat_name": "设计素材/源文件",
    "channel_cat_id": "201454708", "tb_cat_id": "201160807",
}
```

**关键**：把 DTO 作为 `category` 传给 `item_publish`（走 `category_json`）→
**goofish-cli 跳过内部 recommend**，避开失败点。

> 三条 id 缺一不可：`cat_id` / `channel_cat_id` / `tb_cat_id`。
> 想要新类目，就用一个已知能识别的标题去 `category_recommend` 拿 DTO，**不要手编**。

---

## 七、发布成功的完整链路（实测）

```
图片上传 media_upload        → {url, width, height}（alicdn）
↓
类目 category_recommend     → 失败则 FALLBACK_CATEGORY
↓
item_publish(category=DTO,
             images_json, desc,
             price)          → item_id
↓
验证 item_get / item_list    → status="在售"
```
实测上架结果：`1090023063976 / 1092021253157 / 1090021891910` 均「在售」。

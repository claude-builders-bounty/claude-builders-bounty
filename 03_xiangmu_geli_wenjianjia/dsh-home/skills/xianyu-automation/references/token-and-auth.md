# 闲鱼令牌与登录态：签名令牌自愈、边界、以及 goofish-cli 侧的会话刷新

适用：任何用 pyxianyu 直连 mtop 的场景（本项目是 Phase 1 选品）。

## 1. 签名令牌只有 10 分钟有效期（源码事实）

goofish-cli `core/refresh.py` 模块 docstring 明确写着：

> `_m_h5_tk` 只有 10 分钟有效期，服务端在浏览器**活跃访问**闲鱼页面时通过
> `Set-Cookie` 续期；浏览器静默几分钟就会过期。

推论（重要）：
- 从浏览器导出的 Cookie 里那个 `_m_h5_tk`，**在你开始跑程序时大概率已经过期**
- 令牌后缀 `_<ms时间戳>` 是**签发时间**，不是过期时间——不要拿它判断有效性
- 因此「首次请求必然命中一次令牌过期」是**正常现象**，不是配置错误

## 2. 根因：host-only 旧令牌遮蔽服务器新令牌（P0 级阻塞）

### 症状
所有搜索请求返回 `FAIL_SYS_TOKEN_EXOIRED::令牌过期`，即使 Cookie 是刚从浏览器导出的、
甚至同一条 Cookie 两小时前还跑得通。重试也救不回来。

### 机制
`XianyuClient.__init__` 用 `self.session.cookies.update(cookies_dict)` 注入 Cookie。
`RequestsCookieJar.update(dict)` 生成的是 **domain=""（host-only）** 的 cookie。

mtop 在令牌被拒时，会在响应 `Set-Cookie` 里下发一个新令牌，域是 **`.goofish.com`**。
于是 session 里**同时存在两份 `_m_h5_tk`**，一次请求把两份都发给服务端 →
服务端取到旧的那份 → 永远过期。

### 诊断方法（决定性）
打印 session 里全部同名 cookie 及其 domain，而不是只看 `get_cookie_value()`：

```python
for c in client.session.cookies:
    if c.name == "_m_h5_tk":
        print(repr(c.domain), c.value[-14:])
# 典型输出:
#   '<host-only>'      ..._1791929014880   <- 旧（注入的）
#   '.goofish.com'     ..._1791944490550   <- 新（服务器下发的）
```

注意 `XianyuClient.get_cookie_value()` 有 domain 打分逻辑（优先 `goofish.com`），
所以它可能返回新令牌，而**实际发出去的请求仍带着两份**——只看这个函数会被骗。

### 修复
让 session 里只保留服务器最新的那一份：优先 `goofish.com` 域，其次时间戳最大；
清掉其余同名 cookie，再写回单一值。封装见 `src/xianyu_session.py`：

- `sync_server_token(client, force=False)` —— 归一到单一令牌；
  **若一份都没有则注入格式合法的占位令牌**（32 位 hex + `_` + 毫秒时间戳），
  否则签名函数会抛 `XianyuConfigError: 缺少 _m_h5_tk cookie`，重试链路根本没机会启动
- `is_token_expired(exc)` / `is_recoverable_token_error(exc)` —— 判断是否值得重试
- `call_with_token_refresh(client, fn, *args, max_retries=3)` —— 调用失败→归一令牌→重试

接入点：`phase1_selector.initialize()` 里建完 client 立刻 `sync_server_token()`；
搜索调用改用 `call_with_token_refresh(...)` 包一层。

## 3. 服务器对签名令牌的三类拒绝（均实测可自愈）

| 服务器返回 | 触发场景 | 自愈 |
|-----------|---------|------|
| `FAIL_SYS_TOKEN_EXOIRED::令牌过期` | 令牌已被服务器轮换（首请求必命中） | ✅ |
| `FAIL_SYS_TOKEN_ILLEGAL::非法令牌` | 令牌结构被破坏 / 占位令牌 | ✅ |
| `FAIL_SYS_TOKEN_EMPTY::令牌为空` | 令牌缺失或为空 | ✅ |
| `FAIL_SYS_SESSION_EXPIRED::登录失效` | **登录态本身失效** | ❌ 必须重新导出 Cookie |

**匹配用子串**（服务端拼写 `EXOIRED` 少个 P，别「修正」它）：
`TOKEN_EXOIRED` / `TOKEN_EXPIRED` / `TOKEN_ILLEGAL` / `TOKEN_EMPTY` /
`令牌过期` / `非法令牌` / `令牌为空`

占位令牌要写成**合法格式**（hex 前缀 + `_` + 时间戳）。用 `placeholder_<ts>` 这种
非 hex 前缀会得到 `TOKEN_EMPTY` 而不是 `TOKEN_ILLEGAL`，握手更慢。

## 4. 自愈边界：哪些 cookie 会变，哪些不会

请求前后对比 session 内 cookie（实测）：

```
★变化  _m_h5_tk                <- 服务器每次响应轮换
★变化  _m_h5_tk_enc            <- 配套轮换（注意新旧并存导致的重复）
★变化  mtop_partitioned_detect <- 服务器新写入
  不变  cookie2 / unb / _tb_token_ / sgcookie / havana_lgc2_77
        / t / tfstk / tracknick / cna / csg / xlly_s / sdkSilent
```

结论：
- 自愈**只覆盖签名令牌**（`_m_h5_tk` / `_m_h5_tk_enc`）
- **登录态 cookie 不受影响**；它们失效时报 SESSION_EXPIRED 一类错误，只能重导 Cookie

补充实测（反直觉，但别据此去掉登录态字段）：
搜索接口 `mtop.taobao.idlemtopsearch.pc.search` **不校验登录态 cookie** ——
把 `cookie2` / `unb` / `_tb_token_` / `sgcookie` 全改成乱码后，搜索照样返回 20 条。
所以 **Phase 1 对登录态不敏感**；但 Phase 3/4 的发布与私信必然需要真实登录态。

## 5. goofish-cli 侧的登录态自愈（Phase 2/3/4，需系统 Chrome 才能用）

goohish-cli 自带 `core/refresh.py`：遇 token/session 失效时用浏览器访问强鉴权页，
让服务端重新下发完整 session cookie。流程：

1. `goto https://www.goofish.com` → 若弹 `#alibaba-login-box` 登录 iframe，
   自动点 `快速进入`（免密记忆登录）
2. `goto https://www.goofish.com/bought`（强鉴权页）触发服务端下发完整 session
3. 抓 `page.context.cookies()` 作为新快照

关键约束（源码事实，决定部署方式）：
- 刷新成功的必需字段：`_m_h5_tk`、`unb`、**`cookie2`**。
  只更新了 `_m_h5_tk` 而没有 `cookie2` → 视为假成功，函数返回 False（正确行为，别绕）
- 开关：环境变量 `GOOFISH_AUTO_REFRESH_TOKEN=0` 可关闭（默认开启）
- **`core/browser.py` 硬编码 `channel="chrome"`** —— 不支持 Edge，
  也不下载 chromium（`playwright install chrome` 返回 `Install location: <system>`，
  意思是「找系统已装的」）。源码注释说明原因：playwright 自带 bundled chromium 的
  UA/CDP 指纹太裸，是风控高危目标，系统 Chrome 才是真实用户每天在用的可执行
- 默认 **headful**（`launch_persistent_context`，非 headless）。
  源码注明 headless 即便 `channel=chrome` 仍会被判「非法访问」。
  `GOOFISH_HEADLESS=1` 可切 headless（代价是可能被风控）
- 每次调用建独立 tmp profile（`<home>/.goofish-cli/profiles/chrome-<tmp>/`），
  退出清理 —— 为的是避开 Chrome `SingletonLock`，支持并发

因此：**没有系统 Chrome，Phase 2/3/4 的登录态过期就无法自愈**，只能人工重导 Cookie。
Phase 1（pyxianyu 直连）不受影响。

## 6. 验收：不产生真实商品的自检脚本骨架

```python
# 1) 打印 session 内全部 _m_h5_tk 及 domain（确认归一逻辑生效）
# 2) 三种令牌异常各跑一遍，断言最终 ret == SUCCESS::调用成功 且条数 > 0
#    A. .env 原值（已过期）  B. 刻意破坏的令牌  C. 完全删掉 _m_h5_tk
# 3) 断言 is_recoverable_token_error(): 前三种 True, SESSION_EXPIRED False
```

跑完把结果记进项目根目录 `DEBUG_LOG.md`（问题→方案→文件→验证）。

# 百度网盘鉴权与 OAuth2 接入（实测记录）

适用：Phase 2 货源工厂的资源托管（上传 + 生成分享链接）。
标注 ✅ 的为实测通过；标注 ⚠️ 的为**尚未跑通/未验证**，不要当成可行方案照抄。

## 1. 字段映射（最大坑，先看这个）

| 控制台字段 | 值形态 | 用途 |
|---|---|---|
| AppID | 数字（如 `124442982`） | 仅应用编号，**不能**当 OAuth `client_id` |
| AppKey | 字符串 | ✅ OAuth **client_id** |
| SecretKey | 字符串 | ✅ OAuth **client_secret** |
| SignKey | 字符串 | 请求签名用，不参与 OAuth |

把数字 AppID 当 client_id 会得到：

```
错误代码：invalid_client
错误信息：unknown client id
详细描述：应用不存在，请开发者确认传递的client_id参数(即api key)是否正确
```

**这个报错不代表应用被删除/关闭** —— 先怀疑字段填错，不要让用户去控制台重建应用。

## 2. 授权端点：先服务端自检，再麻烦用户

在让用户开浏览器之前，先 GET authorize 端点并解析返回的 HTML，就能验证 client_id 与 redirect_uri 是否合法：

```python
import requests
s = requests.Session()
s.headers.update({"Accept-Encoding": "identity"})   # 见第 6 节
for ru in ["oob", "http://localhost:8080/callback"]:
    r = s.get("https://openapi.baidu.com/oauth/2.0/authorize",
              params={"response_type": "code", "client_id": APP_KEY,
                      "redirect_uri": ru, "scope": "basic,netdisk",
                      "display": "page"},
              timeout=10, allow_redirects=False)
    # ✅ 通过：返回登录页（约 8k 字符，页面里没有错误串）
    # ❌ 失败：HTML 里出现 redirect_uri_mismatch / unknown client id
```

实测结果：

| redirect_uri | 结果 |
|---|---|
| `oob` | ✅ 通过 —— 用户授权后**页面直接显示授权码**，不需要回调服务器，WSL 场景首选 |
| `http://localhost:8080/callback` | ✅ 通过（已在控制台注册） |
| `https://localhost:8080/callback` | ❌ `redirect_uri_mismatch` / Invalid redirect uri |

回调地址必须**逐字符**匹配控制台注册值（协议 / 端口 / 路径），`http` ≠ `https`。

## 3. 设备码流程：端点存在，但这个应用没开通 ⚠️

```http
POST https://openapi.baidu.com/oauth/2.0/device/code
  response_type=device_code      # 注意是 response_type，不是 grant_type
  client_id=<AppKey>
  scope=basic,netdisk
```

→ 返回 `device_code / user_code / verification_url(https://openapi.baidu.com/device) / qrcode_url / expires_in=300 / interval`

但用 device_code 换 token **全部失败**：

| 尝试 | 返回 |
|---|---|
| `grant_type=device_code` | `unsupported_grant_type` |
| `grant_type=urn:ietf:params:oauth:grant-type:device_code` | `unsupported_grant_type` |
| `grant_type=authorization_code` + `code=<device_code>` | `invalid_grant: invalid code , expired or revoked` |

结论：该应用的 token 端点未开通 device_code grant。设备码只能用于「扫码登录」，**不能**完成 OAuth token 交换 —— 不要把设备码流程当主路径。

**不用真的授权就能判别 grant_type 是否被支持**（很有用）：

| 返回 | 含义 |
|---|---|
| `unsupported_grant_type` | 该 grant_type 不被支持 |
| `invalid_request: missing required parameter` | grant_type **被接受**，只是缺参数 |
| `invalid_grant: invalid code , expired or revoked` | 参数齐了但 code 无效 |

⇒ 由 `grant_type=authorization_code` 缺 `redirect_uri` 时报 `invalid_request` 可知：**交换时必须带 redirect_uri**。

## 4. 授权码流程（选定路径）⚠️ 交换未端到端实测

授权 URL（`redirect_uri=oob`，用户授权后页面直接显示 code）：

```
https://openapi.baidu.com/oauth/2.0/authorize?response_type=code&client_id=<AppKey>&redirect_uri=oob&scope=basic%2Cnetdisk&display=page
```

交换：

```http
POST https://openapi.baidu.com/oauth/2.0/token
  grant_type=authorization_code
  code=<授权码>
  client_id=<AppKey>
  client_secret=<SecretKey>
  redirect_uri=oob        # 必须与授权时一致
```

预期返回 `access_token / refresh_token / expires_in(~30 天) / scope`。
刷新：`grant_type=refresh_token&refresh_token=...&client_id&client_secret`。

脚本：`scripts/baidu_exchange_code.py`（`--refresh` 刷新、`--check` 验证 token、自动写回 `config/.env`）

**⚠️ 状态说明**：脚本已写好，但会话结束于「等用户粘贴授权码」，**交换从未真实跑通**。第一次拿到真 code 后必须核对：
1. 返回是否含 `access_token`；
2. `GET https://pan.baidu.com/rest/2.0/xpan/nas?method=uinfo&access_token=<at>` 是否返回用户信息；
3. `redirect_uri` 是否必须与授权时完全一致（oob ↔ oob）。

## 5. Cookie（BDUSS/STOKEN）能做到哪一步

| 操作 | BDUSS/STOKEN cookie |
|---|---|
| list / search / download / delete / rename | ✅ 实测可用 |
| upload（Web 端点 `c.pcs.baidu.com` / `d.pcs.baidu.com` multipart） | ⚠️ 实测 `errno 2`，未跑通 |
| quota / share_create | ❌ 报 need access_token |
| share_list | 需要 STOKEN（未单独验证） |

结论：cookie 只能兜底元数据类操作；**上传 + 分享链接必须走 OAuth2 access_token**。

## 6. 依赖与传输坑

- `pip install baidupcs-py`（PeterDing/BaiduPCS-Py，875★）在 Python 3.12 上装不上：pin 了 `Pillow<9`，构建失败。读它源码作 API 形态参考可以，别装。
- 自研 `requests` 客户端（零三方依赖）是这个场景的可行替代。
- Baidu 端点对 `Accept-Encoding` 处理不稳，典型症状是 **HTTP 200 但 body 为空**。统一加 `Accept-Encoding: identity` 解决。

## 7. 省用户时间的排查顺序

1. 服务端探针验 authorize（client_id 字段对不对、redirect_uri 注册没注册）；
2. 再让用户开浏览器拿 code；
3. 拿到 code **立刻**交换（code 约 10 分钟过期，别拖）。

## 8. 工作方式教训（用户明确不满过）

- **用户主动说「我可以授权」时立刻办**：不要为了追求全自动而继续找绕路方案、让用户干等。一次性人工授权成本极低。
- OAuth 接入先查官方控制台/文档的**字段映射**，再写代码；不确定就先用第 2 节探针自检，别把错误配置直接丢给用户去浏览器里踩。
---
name: baidu-netdisk-pcs-upload-share
description: "百度网盘上传+分享：PCS/BDUSS 或官方 bdpan 通道。"
version: 0.2.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [baidu, netdisk, upload, share, pcs, bdpan, errno-115]
    related_skills: [xianyu-automation, evidence-backed-deliverables]
---

# 百度网盘程序化上传 + 分享链接

## 触发场景
- 需要用脚本/Agent 自动上传文件到百度网盘
- 需要自动生成网盘分享链接 + 提取码（如闲鱼自动发货）
- 遇到 `errno=31500`、`error_code=31024 app id is empty`、`unsupported_grant_type`

## 核心结论（血泪教训）

**不要用 xpan 开放平台接口做上传/分享。** 走 PCS 老接口 + BDUSS 查询参数。

| 方案 | 认证 | 上传 | 分享 | 结论 |
|------|------|------|------|------|
| xpan `pan.baidu.com/rest/2.0/xpan/file` | OAuth2 access_token | ❌ errno 31500（应用未开通上传权限） | ❌ 无权限 | 弃用 |
| xpan `precreate` | access_token | 返回 `return_type=1` 但**无 uploadid** → 无法 create | — | 弃用 |
| **PCS `pcs.baidu.com/rest/2.0/pcs/file`** | **BDUSS 作查询参数** | ✅ | ✅ 配 `share/set` | **采用** |
| Web 网页接口 (bdstoken) | Cookie | 同 xpan 症状 | ✅ `pan.baidu.com/share/set` | 分享用 |

## 关键参数（缺一不可）

```python
PCS_FILE  = "https://pcs.baidu.com/rest/2.0/pcs/file"
PCS_QUOTA = "https://pcs.baidu.com/rest/2.0/pcs/quota"
PCS_APP_ID  = "778750"      # 必须！缺了报 31024 app id is empty
PAN_APP_ID  = "250528"      # pan.baidu.com 接口用
PCS_UA      = "softxm;netdisk"   # 必须伪装官方客户端
```

- **BDUSS 走查询参数**（不是 Cookie）：`params={"BDUSS": bduss, "app_id": "778750"}`
- STOKEN 走 Cookie，`share/set` 需要
- UA 必须 `softxm;netdisk`，否则被拒

## 上传（单请求，无需 precreate/create）

```python
r = session.post(
    PCS_FILE,
    params={"method": "upload", "ondup": "overwrite",
            "dir": "/xianyu_resources", "filename": "a.zip",
            "BDUSS": bduss, "app_id": "778750"},
    files={"file": ("a.zip", open(local, "rb"), "application/octet-stream")},
    timeout=1800,
)
# → {"path": ..., "fs_id": 123, "size": ..., "md5": ...}
```
返回的 `fs_id` 是后续分享的必需参数。

## 生成分享链接 + 提取码

```python
# 1. 取 bdstoken
r = session.get("https://pan.baidu.com/api/gettemplatevariable",
    params={"app_id":"250528","channel":"chunlei","clienttype":"0","web":"1",
            "fields":'["bdstoken"]'})
bdstoken = r.json()["result"]["bdstoken"]

# 2. 创建分享
r = session.post("https://pan.baidu.com/share/set",
    params={"channel":"chunlei","clienttype":"0","web":"1",
            "bdstoken":bdstoken,"app_id":"250528"},
    data={"fid_list": json.dumps([fs_id]),
          "channel_list": "[]",
          "period": "0",            # 0=永久
          "pwd": "a1b2",            # 4位，留空则无码
          "schannel": "4" if pwd else "0"},   # 4=带提取码
    headers={"Referer":"https://pan.baidu.com/disk/main"})
# → {"errno":0, "link":"https://pan.baidu.com/s/1xxx", "shareid":...}
```

注意：响应里的 `pwd` 字段可能不回显，用 `j.get("pwd") or 传入的pwd` 兜底。

## 其他常用 PCS 方法（GET/POST 与参数格式极易踩坑）

| 操作 | HTTP | method | 参数 |
|------|------|--------|------|
| 列目录 | **GET** | `list` | `path=/` + `by=name` + `order=asc` |
| 搜索 | **GET** | `search` | `path=/`, `wd=关键词`, `re=1` |
| 建目录 | **GET** | `mkdir` | `path=/a/b` |
| 容量 | **GET** | `quota/info` | — |
| 取元信息 | POST | `meta` | `param` = `{"list":[{"path":"/a.zip"}]}` → 拿 fs_id |
| 删除 | POST | `delete` | `param` = `{"list":[{"path":"/a"}]}` |
| 重命名 | POST | `rename` | `param` = `{"list":[{"path":"/a","newname":"b"}]}` |

### 三个致命参数坑

1. **`param` 必须包一层 `{"list": [...]}`**
   ```python
   # ❌ 裸数组 → error_code=31023 param error
   param = json.dumps([{"path": "/a"}])
   # ✅
   param = json.dumps({"list": [{"path": "/a"}]})
   ```

2. **`limit` 参数已废弃 —— 传了就报 31023**
   ```python
   # ❌ BaiduPCS-Py 老写法，现在必然失败
   {"method":"list","path":"/","by":"name","order":"asc","limit":"0-2147483647"}
   # ✅ 直接省略 limit，默认返回全部（实测根目录返回 50 条）
   {"method":"list","path":"/","by":"name","order":"asc"}
   ```

3. **读操作用 GET，写操作才用 POST**
   - `list` / `search` / `mkdir` 走 GET（POST 会 31023）
   - `delete` / `rename` / `meta` / `upload` 走 POST

### 其他错误码

| 错误码 | 含义 | 处理 |
|--------|------|------|
| `31045 user not exists` | 没带登录态 Cookie（BDUSS 查询参数单独不够） | session 里同时设 BDUSS(.baidu.com) + STOKEN(pan.baidu.com) + UA + Referer |
| `31061 file already exists` | 目录已存在 | `makedir` 视为成功（幂等） |
| `31023 param error` | 参数格式错（见上面三个坑） | 按上述修 |

> BDUSS **既作查询参数又作 Cookie**（双保险）；单靠查询参数在新接口上会 `31045`。

## OAuth2 踩坑（仅在需要 access_token 时）

- **`client_id` 填 AppKey（字符串），不是 AppID（数字）** —— 填 AppID 报 `invalid_client: unknown client id`
- 设备码流程：`response_type=device_code`（不是 grant_type），但很多应用**未开通 device_code grant** → 报 `unsupported_grant_type`
- 授权码流程可靠：`https://openapi.baidu.com/oauth/2.0/authorize?response_type=code&client_id=<AppKey>&redirect_uri=oob&scope=basic,netdisk`
  - `redirect_uri=oob` 页面直接显示授权码，**不需要回调域名**（Baidu 桌面应用规范）
  - 校验 redirect_uri 是否注册：请求后看页面有无 `redirect_uri_mismatch`
- token 交换：`POST https://openapi.baidu.com/oauth/2.0/token` `grant_type=authorization_code&code=&client_id=<AppKey>&client_secret=<SecretKey>&redirect_uri=oob`，有效期 30 天

## errno=115 有两种成因，别混（实测）

`errno=115` 出现在 `share/set` 阶段（上传已成功、`fs_id` 已分配），读 **`show_msg`** 而不是 `errmsg`。本周两次真实事故，根因完全不同：

| 成因 | 判据 | 修法 |
|---|---|---|
| **重复发布**（状态文件丢失/未迁移） | 同一 `fs_id` 或同一路径之前已分享过；日志里能看到重复下载/重复上传 | 找回 `published_registry.json` / `upload_records.json` 等已发布缓存，走「跳过已发布」分支；重跑应报 `reused: N` 而不是再分享 |
| **账号级限制**（`errno=115 账号异常，禁止分享`） | 换新文件、换目录仍 115；重试与等待无效 | 放弃 PCS/BDUSS 分享，改走**官方 bdpan OAuth 通道**（`NETDISK_BACKEND=bdpan`，实现文件 `src/netdisk_bdpan.py`） |

迁移机器时先查第一种 —— 状态文件没搬过来会让「已发布」变成「重复发布」，看起来像账号被封。只有排除第一种之后才改通道。

通道选择的推荐形态：默认官方通道优先、BDUSS 回退；两个方向都能用环境变量强制（`NETDISK_BACKEND=bdpan|baidu`）。改完必须真跑一次 `publish --limit 1` 拿到分享链接才算验证，不要只看代码分支。

## 高频错误速查

| 现象 | 原因 | 修法 |
|------|------|------|
| `error_code=31024 app id is empty` | PCS 请求缺 app_id | 加 `app_id=778750` |
| `errno=31500` | 用了 xpan 且应用无上传权限 | 换 PCS 接口 |
| `errno=115`（`share/set`） | 重复分享 或 账号禁止分享（两种，见上一节） | 先补状态文件，再改 bdpan 通道 |
| `errno=31061 file already exists` | 目录已存在 | `mkdir` 视为成功（幂等） |
| `unsupported_grant_type` | 应用未开通 device_code | 改用授权码 + oob |
| `invalid_client: unknown client id` | client_id 填了 AppID | 改填 AppKey |
| `errno=2` 参数错误 | Web 上传签名校验严 | 别自己拼 web 上传，用 PCS |
| `return_type=1` 但无 uploadid | xpan precreate 被降级 | 换 PCS 单请求上传 |
| 响应空 body + 200 | 加了 Accept-Encoding gzip | 设 `Accept-Encoding: identity` |
| `errno=105`（share/verify） | 百度对该接口加了验证码风控 | 不影响买家浏览器访问，忽略 |

## 验证清单

1. `method=upload` 返回带 `fs_id` → 上传成功
2. `share/set` 返回 `errno=0` + `link` → 分享成功
3. 匿名 GET 分享页：`uk=0` 表示需要提取码（正常）
4. 开源参考：BaiduPCS-Py `baidupcs_py/baidupcs/pcs.py`（PCS_APP_ID/PCS_UA 出处）
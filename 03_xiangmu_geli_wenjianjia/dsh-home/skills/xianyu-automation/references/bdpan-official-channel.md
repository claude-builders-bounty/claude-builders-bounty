# 百度网盘官方通道（bdpan CLI / OAuth）—— errno=115 的解法

## 何时用

`netdisk_baidu.py`（BDUSS + PCS 网页接口）返回：

```json
{"errno":115,"show_msg":"账号异常，禁止分享"}
```

这是**账号级限制**，重试/刷 bdstoken **无效**。改用官方 OAuth 通道。

## 官方 skill 与 CLI

- 仓库：`baidu-netdisk/bdpan-storage`（Apache 2.0，官方）
- Skill 安装位置：`<hermes>/skills/productivity/baidu-drive/`
- CLI：`bdpan.exe`，装到 `~/.local/bdpan/versions/<ver>/bdpan.exe`
- 认证：OAuth 2.0（`openapi.baidu.com`），**不是** BDUSS
- 作用域：**硬限制 `/apps/bdpan/`**（用户视角「我的应用数据/bdpan/」）

## 安装

```bash
# 官方安装脚本自动检测平台（含 MINGW*/MSYS*/CYGWIN* → windows-amd64）
# 内置 SHA256 校验
bash <skill>/scripts/install.sh --yes
```

实测 SHA256（windows-amd64 / installer 3.8.4）：
`194f5174bbb3d9260cc5b7d465c4f98d6b9279e028db136dc1e57cc3bc1f49a0`

**下载源坑**：`codeload.github.com` 空响应、`raw.githubusercontent.com` 连接重置 →
用 jsDelivr 镜像：`https://cdn.jsdelivr.net/gh/<owner>/<repo>@main/<path>`

**curl 坑**：curl 是原生程序，MSYS 路径不转换。
`curl -o /tmp/x` → `Failed to open the file`(errno 23)。
**必须 `cd` 到目标目录后用相对路径**。

## 登录（OOB 设备码流程，适合无 GUI Agent）

```bash
bash <skill>/scripts/login.sh
# 1) 确认安全须知 -> 2) 打印授权 URL + Markdown 链接
# 3) 用户在浏览器授权 -> 得到 32 位 hex 授权码 -> 回填
```

**驱动 PTY 的坑**：脚本第一步 `read -n 1 -r`（单字符，不需要回车）。
若用「文本+回车」提交，残留的 `\n` 会被后续 `read -r -s AUTH_CODE` 吃掉 →
报「授权码不能为空」。
**正确做法**：确认那步用 `write`（无换行）发 `y`；授权码那步用 `submit`。

## Python 封装

`src/netdisk_bdpan.py`（`BdpanNetdisk`）接口与 `BaiduNetdisk` 对齐：
`makedir / upload / wait_fs_ready / create_share / list / upload_and_share`

要点：
- 定位二进制：PATH → `~/.local/bdpan/current-version` → versions 目录 → `%LOCALAPPDATA%\bdpan`
- `_run()` 必须处理 **list 型 JSON**（`bdpan ls` 返回数组，对其调 `.get()` 会
  `'list' object has no attribute 'get'`）
- 路径：CLI 只吃**相对 `/apps/bdpan/` 的相对路径**；`/xianyu_resources` 会被归一化为
  `xianyu_resources` → 实际落在 `/apps/bdpan/xianyu_resources`
- **`bdpan share` 只接受路径，不接受 fs_id**（需先反查）→ 调用方应优先传 `remote_paths`
- 公共参数必须带：`--agentname` / `--session-input` / `--session-id`（格式 `{ts}-{6随机}`）

## 接入管线

`factory_publish.py` 的网盘后端选择：

```
NETDISK_BACKEND=bdpan  -> 强制官方 OAuth
NETDISK_BACKEND=baidu  -> 强制 BDUSS/PCS
（未设）              -> 官方优先，不可用时自动回退 BDUSS
```

## 实测结果

| 项 | BDUSS/PCS | 官方 bdpan |
|---|---|---|
| 上传 | ✅ | ✅ `code:0` + fsid |
| 分享 | ❌ errno=115 账号异常 | ✅ 返回 link + pwd |
| Phase 2.5 批量 | `{'failed': 2}` | `{'published': 2}` |

**注意**：本次成功的账号与受限账号**不是同一个**，所以不能严格证明
「官方接口绕过账号限制」—— 更可能是换了未受限账号。要严格验证需用受限账号授权。

## 其它约束

- 分享有效期只支持枚举：`0`(永久) / `1` / `7` / `30` 天
- 删除（`bdpan rm`）需用户明确确认；不主动建议删除
- 不读不写 `~/.config/bdpan/config.json`（含 access_token）

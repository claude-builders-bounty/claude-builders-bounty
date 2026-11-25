---
name: xianyu-automation
description: 闲鱼（Goofish）自动化运营：使用 pyxianyu 库实现选品、货源、上架、发货全流程自动化
category: ecommerce-automation
tags: [xianyu, goofish, pyxianyu, automation, ecommerce]
version: 1.0.0
---

# Xianyu Automation with pyxianyu

闲鱼（Goofish）自动化运营技能：使用 `pyxianyu` 库实现选品、货源、上架、发货全流程自动化。

## 触发条件
- 需要在闲鱼平台自动化：选品监控、商品发布、订单发货、消息回复
- 需要处理闲鱼 Cookie、WebSocket 长连接、MTOP 签名
- 需要规避风控：敏感词替换、随机间隔、一机一号

## 核心依赖
```bash
# goofish-cli 是 pip 包（不是 npm！），提供 goofish / goofish-cli / goofish-mcp 三个命令
# 源: https://github.com/fancyboi999/goofish-cli
pip install pyxianyu goofish-cli pandas openpyxl requests playwright pyyaml \
            python-dotenv loguru tenacity tqdm openai mcp
```

**依赖清单易漏项（都踩过）**：
- `goofish-cli` —— Phase 2/3/4 的 MCP 服务端，原 `requirements.txt` 没写，必须显式装
- `openai` —— Phase 1 的 `phase1_selector` 顶层 import，原 `requirements.txt` 也没写
- `playwright` + `browser-cookie3` —— goofish-cli 的依赖，会连带装 `pywin32`/`wmi`
- 装完跑 `python -m playwright install chromium`

**验证 goofish-cli 可用**：`venv\Scripts\goofish-cli.exe --help`
会提示「is an MCP stdio server and cannot be used interactively」——
**这是正常的**，说明装好了（用 `goofish --help` 看 CLI）。

## 关键初始化代码（避坑版）

```python
from pyxianyu import XianyuClient
from pyxianyu.apis import SearchApi, ItemApi

# 1. Cookie 字符串 -> dict
def parse_cookie_string(cookie_str: str) -> dict:
    cookie_dict = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookie_dict[k.strip()] = v.strip()
    return cookie_dict

# 2. 初始化客户端（注意参数名是 cookies 复数，且需 dict）
cookie_dict = parse_cookie_string(xianyu_cookie_string)
client = XianyuClient(cookies=cookie_dict, device_id="auto")

# 3. 直接使用，无需 __aenter__/__aexit__
search_api = SearchApi(client)
item_api = ItemApi(client)

# 4. 搜索商品 —— 注意：search_items 是【同步】方法，不能 await！
result = search_api.search_items(
    keyword="PPT模板",
    page_number=1,
    rows_per_page=20,
)
# 实测返回: {'ret': ['SUCCESS::调用成功'], 'data': {'resultList': [{'data': {'item': {...}}}]}}
# 真实字段路径:
#   标题  item['main']['exContent']['detailParams']['title']
#   价格  item['main']['exContent']['detailParams']['soldPrice']   <-- 干净字符串 '1.58'
#         （exContent['price'] 是富文本分片 [{text:'¥'},{text:'1'},{text:'.58'}]，别直接 float）
#   卖家  item['main']['exContent']['detailParams']['userNick']
#   想要  item['main']['exContent']['fishTags']['r3']['tagList'][0]['data']['content'] -> '375人想要'
#   图片  item['main']['exContent']['picUrl']
#   地区  item['main']['exContent']['area']

# 4. 发布商品
await item_api.publish_item(publish_payload)

# 5. 发货/回复消息 - 需配合 XianyuLive (WebSocket)
```

## Cookie 必需字段
从浏览器 F12 -> Application -> Cookies -> goofish.com 获取，**必须包含**：
- `_m_h5_tk` - MTOP 签名 token
- `_m_h5_tk_enc` - 加密 token
- `cookie2` - 二代 cookie
- `t` - 时间戳
- `cna` - 设备指纹
- `xlly_s` - 登录态标识
- `_tb_token_` - 淘宝 token

## 硬超时保护（防定时任务卡死）

**文件**：`src/timeout_utils.py` + 各 Phase 入口注入

**全局配置**（可通过环境变量覆盖）：
| 常量 | 默认值 | 说明 |
|------|--------|------|
| `XY_PIPELINE_TIMEOUT` | 3600s (60min) | 全流水线总超时（pan-search 耗时长） |
| `XY_PHASE1_TIMEOUT` | 600s (10min) | 选品雷达 |
| `XY_PHASE2_TIMEOUT` | 3600s (60min) | 货源工厂（含 pan-search 17 类目 × 多关键词） |
| `XY_PHASE25_TIMEOUT` | 1200s (20min) | 落地发布 |
| `XY_PHASE3_TIMEOUT` | 600s (10min) | 自动上架 |
| `XY_PHASE4_POLL_TIMEOUT` | 30s | Phase 4 单轮轮询 |
| `XY_MCP_TIMEOUT` | 120s | 单次 MCP 调用（pan-search 慢） |
| `XY_SEARCH_TIMEOUT` | 120s | 单页搜索 / pan-search 单类目 |
| `XY_DOWNLOAD_TIMEOUT` | 300s | 单文件下载 |
| `XY_UPLOAD_TIMEOUT` | 300s | 单文件上传 |
| `XY_NETDISK_SHARE_TIMEOUT` | 120s | 分享创建 |

**pan-search 实测耗时参考**（ENABLE_PAN_SEARCH=1）：
- 17 个类目 × 平均 4-6 关键词/类目
- 单关键词 ~10-15s，单类目 ~60-90s
- 全量跑完 ~15-20 分钟
- **必须把 XY_PHASE2_TIMEOUT 和 XY_SEARCH_TIMEOUT 调大**，否则会被硬超时切断

**GitHub Awesome 列表采集**：需要真实 `GITHUB_TOKEN`（config/.env），否则全部 403 返回 0 条。占位符 `ghp_xxx` 无效。

**使用模式**：
```python
from src.timeout_utils import with_timeout, PHASE1_TIMEOUT

# 装饰器式
@timeout_protected(PHASE1_TIMEOUT, "Phase1:search")
async def search_keyword(...):
    ...

# 上下文管理器式
async with timeout_context(30, "search_page") as ctx:
    result = await ctx.protect(coro)

# 批量带总超时
await gather_with_timeout(*coros, timeout=600, operation="batch", max_concurrent=3)
```

**已注入位置**：
- `main.py`：`run_full_pipeline` / `run_phase1_selection` / `run_phase2_factory` / `run_phase2_publish` / `run_phase3_listing` / `run_phase4_delivery`
- `phase1_selector.py`：`search_keyword` 单页搜索
- `phase2_factory.py`：`fetch_github_awesome` / `fetch_official_sources` / `fetch_competitor_resources` / `run_factory`
- `phase4_delivery`：单轮轮询 30s 超时

> **关键规则**：每个 `await` 外层加 `asyncio.wait_for`；全流水线加 `asyncio.timeout` (Python 3.11+) 或自定义 `wait_for`；Phase 4 必须加心跳+看门狗。

```python
def extract_last_json(text: str):
    end = text.rfind('}')
    if end == -1: return None
    brace_count = 0
    start = -1
    for i in range(end, -1, -1):
        if text[i] == '}': brace_count += 1
        elif text[i] == '{':
            brace_count -= 1
            if brace_count == 0:
                start = i
                break
    if start != -1: return text[start:end+1]
    return None

json_str = extract_last_json(content + reasoning_content)
if json_str: return json.loads(json_str)
```

## 敏感词替换（规避风控）
发布前必须替换：
```python
SENSITIVE_WORD_MAP = {
    "课程": "资料包", "教程": "学习合集", "破解": "绿色版",
    "盗版": "非官方", "百度网盘": "某盘", "网盘链接": "下载地址",
    "电子版": "数字版", "PDF版": "文档版"
}
```

## 长任务交互约定（用户明确要求，每次长跑都适用）

本流水线单轮 15-25 分钟，用户会反复问「怎么停了？」「你到底在跑没有」。必须让状态一眼可判：

- **没跑完不要收尾**：不要在两次工具调用之间丢一句看起来像总结的散文。用户会把
  「我跑一下」后的短句读成「它停了，在等我」。
- **运行中只说状态**：一句「正在后台跑，已 N 秒，等它完」就够；不要附结论文案。
- **说出「收工」才算停**：只有真正完成后才给完整汇报（结果表 + 待办 + 下一步），
  并以「收工」或明确的完成标记结束。
- **不要在同一轮里既改代码又写收尾语**。
- 长跑用后台进程 + `notify_on_complete`，并在等待空窗里做不依赖它的活，别反复空等。

一句话判据：**没说出「已停 / 待你指令」就是在跑。**

## 反爬间隔
```python
await asyncio.sleep(random.uniform(1.5, 3.0))  # 每页间隔
```

## 完整流水线架构
```
Phase 1: 选品雷达  -> Phase 2: 货源工厂 -> Phase 2.5: 落地发布 -> Phase 3: 自动上架 -> Phase 4: 自动发货
   pyxianyu搜索        GitHub+官方源+网盘      下载→加工→网盘上传→分享   模板化标题/SKU/主图   WebSocket+轮询双通道
      规则评分          法律闸过滤/去重         差异化处理/水印/打包       真实数量透传/合规自检   卡密原子预占/自动好评
```

## Windows 原生化 = 整套迁移生产版（不要手写 pyxianyu-only 精简版）

**正确做法**：Windows 原生化是把 WSL2 的生产版**整套搬过来**，不是另写一个
「只用 pyxianyu、绕开 goofish-cli/MCP」的精简版。`goofish-cli` 是 **pip 包**
（不是 npm 包），Windows 上完全可用，Phase 2/3/4 全靠它。

> 反面教材（实测踩过，被用户否掉）：按「Windows 原生就该绕开 MCP」的思路手写了
> 一个 pyxianyu-only 的 `main.py`（Phase 1 能跑，Phase 2/3 全是模拟桩），
> 用户直接驳回——「我就是让你把 wsl2 的生产级配置移植过来」。
> **不要重新发明，要搬。**

**Project location**: `D:\Ai\Agent\xiangmu\xianyu_pipeline\`

**Key differences from MCP version**:
| Aspect | MCP Version (WSL2) | Windows Native (pyxianyu direct) |
|--------|-------------------|----------------------------------|
| Transport | MCP stdio → goofish-cli | Direct HTTP to h5api.m.goofish.com |
| Cookie handling | Encrypted `~/.goofish-cli/cookies.json` | Plain dict from `.env` `XIANYU_COOKIE` |
| Token refresh | goofish-cli auto-refresh | Manual `_m_h5_tk` sign per request |
| Item publish | `item_publish` MCP tool | `ItemApi.publish_item()` async |
| Search | `search_items` MCP tool | `SearchApi.search_items()` sync |
| Dependencies | goofish-cli, MCP server | `pyxianyu` only |
| Deployment | systemd user timer | Windows Task Scheduler (SYSTEM) |

**Core initialization (Windows native)**:
```python
from pyxianyu import XianyuClient
from pyxianyu.apis import SearchApi, ItemApi
import asyncio

# 1. Cookie 字符串 -> dict (from .env XIANYU_COOKIE)
def parse_cookie_string(cookie_str: str) -> dict:
    cookie_dict = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookie_dict[k.strip()] = v.strip()
    return cookie_dict

# 2. 初始化客户端
cookie_dict = parse_cookie_string(os.getenv("XIANYU_COOKIE"))
client = XianyuClient(cookies=cookie_dict, device_id="auto")
search_api = SearchApi(client)  # 同步，不可 await
item_api = ItemApi(client)      # 异步，需 await

# 3. 搜索 (同步)
result = search_api.search_items(keyword="PPT模板", page_number=1, rows_per_page=20)

# 4. 发布 (异步)
await item_api.publish_item(publish_payload)
```

**MTOP 签名算法 (每次请求必签，Windows 原生版必需)**:
```python
import hashlib, time, json

def sign_request(token: str, payload: dict, app_key: str = "34839810") -> tuple:
    t = str(int(time.time() * 1000))
    data = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    sign = hashlib.md5(f"{token}&{t}&{app_key}&{data}".encode()).hexdigest()
    return t, sign

# 请求头需带: t, sign, appKey
# 响应 Set-Cookie 会回新的 _m_h5_tk / _m_h5_tk_enc，必须保存配套更新 .env
```

**环境变量最小集** (Windows 原生版，无 MCP/网盘/BDUSS):
```env
XIANYU_COOKIE="_m_h5_tk=xxx; _m_h5_tk_enc=xxx; cookie2=xxx; t=xxx; cna=xxx; xlly_s=xxx; _tb_token_=xxx"
OPENAI_API_KEY="nvapi-xxx"          # NVIDIA Nemotron
OPENAI_BASE_URL="https://integrate.api.nvidia.com/v1"
OPENAI_MODEL_NAME="nvidia/nemotron-3-ultra-550b-a55b"
DAILY_LIST_LIMIT=10
SKU_PRICE_TEMPLATES='{"PPT": [...], "默认": [...]}'
TITLE_TEMPLATES='["{count}套{keyword}...", "..."]'
SENSITIVE_WORD_MAP='{"课程": "资料包", "百度网盘": "某盘", ...}'
```

**统一入口 `main.py` 子命令** (Windows 原生版):
| 命令 | 说明 |
|------|------|
| `run --pages N --limit M` | **全自动 Phase 1-3**：选品→货源清单→落地发布(模拟)→自动上架 |
| `select --pages N` | 仅 Phase 1：选品雷达 |
| `factory --selection-csv <path>` | 仅 Phase 2：货源工厂 |
| `publish --manifest <path> --limit M` | 仅 Phase 2.5：落地发布 (模拟网盘分享链接) |
| `list --manifest <path> --limit M` | 仅 Phase 3：自动上架 (pyxianyu 直发) |
| `menu` | 交互式菜单（含配置向导） |

**关键前置条件** (Windows 原生版，缺一不可):
| 条件 | 检查命令 | 通过标准 |
|------|----------|----------|
| 闲鱼 Cookie | `type config\.env | findstr XIANYU_COOKIE` | 非空，含 `_m_h5_tk` `cookie2` 等 |
| NVIDIA API Key | `type config\.env | findstr OPENAI_API_KEY` | 非空 |
| Python venv | `dir venv\Scripts\python.exe` | 存在 |
| pyxianyu | `venv\Scripts\python -c "import pyxianyu"` | 无报错 |

## 项目结构与统一入口
项目位于 `/home/user01/.hermes/python/xianyu_pipeline/`（WSL2 开发沙箱），Windows 访问路径 `\\wsl.localhost\Ubuntu-24.04\home\user01\.hermes\python\xianyu_pipeline\`。

### 统一入口 `main.py` 支持的子命令
| 命令 | 说明 |
|------|------|
| `run --pages N --limit M --listing-mode api` | **全自动 Phase 1-3**：选品→货源→落地发布→自动上架（默模式即 api） |
| `select --pages N` | 仅 Phase 1：选品雷达 |
| `factory --selection-csv <path>` | 仅 Phase 2：货源工厂 |
| `publish --manifest <path> --limit M` | 仅 Phase 2.5：落地发布（下载/加工/网盘上传/分享） |
| `list --factory-manifest <path> --mode api` | 仅 Phase 3：自动上架（api=直发，fishops=导出CSV） |
| `deliver --mode standalone` | Phase 4：自动发货服务（长期后台运行） |
| `menu` | 交互式菜单（含配置向导） |

### 关键前置条件（缺一不可）
| 条件 | 检查命令 | 通过标准 |
|------|----------|----------|
| 闲鱼 Cookie | `echo $XIANYU_COOKIE` | 非空，含 `_m_h5_tk` `cookie2` 等 |
| 百度网盘 BDUSS | `echo $BAIDU_BDUSS` | 非空 |
| MCP 配置 | `cat config/mcp_config.json` | 含 goofish-cli server |
| goofish-cli 可用 | `goofish-cli --help` | 无报错 |

### 环境变量配置模板
见 `config/.env.example`，核心变量：
- `XIANYU_COOKIE` - 闲鱼完整 Cookie 字符串
- `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL_NAME` - NVIDIA Nemotron API
- `BAIDU_BDUSS` - 百度网盘 BDUSS
- `NETDISK_TYPE=quark` / `NETDISK_COOKIE` - 网盘类型与 Cookie
- `DAILY_LIST_LIMIT=10` - 每日上架上限
- `SKU_PRICE_TEMPLATES` / `TITLE_TEMPLATES` - 价格与标题模板（JSON）
- `SENSITIVE_WORD_MAP` - 敏感词替换映射
- `DELIVERY_MODE=xianyusmart` / `DELIVERY_CONTENT_MODE=netdisk` - 发货模式

## 常见报错与修复

| 报错 | 原因 | 修复 |
|------|------|------|
| `unexpected keyword argument 'cookie'` | 参数名是 `cookies` 复数 | 改为 `cookies=dict` |
| `'XianyuClient' object has no attribute '__aenter__'` | 不是异步上下文管理器 | 直接实例化，无需 `__aenter__` |
| `not enough values to unpack` | cookies 传了字符串 | 先用 `parse_cookie_string` 转 dict |
| `not enough values to unpack (expected 2, got 1)` | cookie 字符串格式错误 | 检查分号分隔、等号分隔 |

## goofish-cli（MCP 服务端）登录态 —— 最大的坑（已实测）

**症状**：`auth_status` 返回 `valid: true, unb: ...`，但 `item_list` /
`item_publish` / `category_recommend` 全部报 `FAIL_SYS_TOKEN_EXOIRED::令牌过期`。

**两个独立原因，都要修**：

1. **goofish-cli 不读 `XIANYU_COOKIE` 环境变量做实际请求**。它把登录态存在
   **加密的 `~/.goofish-cli/cookies.json`**（无法手改）。env 变量只在
   `auth_login` 时被读取。旧的 `cookies.json` 会一直生效 ->
   必须显式导入：
   ```python
   # 通过 MCP 调用
   auth_login(source="<完整 cookie 字符串>", raw=True)
   # 返回: {"ok": true, "cookies_count": 17, "cookie_file": "/home/user01/.goofish-cli/cookies.json"}
   auth_status()   # 之后才是 valid: true 且能真实调用
   ```

2. **mtop `_m_h5_tk` 每次请求都会轮换**。从浏览器导出的 token 在导出那一刻
   起就可能在服务端失效（Firefox/Chrome 后续请求已把它轮换掉）。
   注意它的时间戳后缀**不代表过期时间**——实测 `_1791818920650` 表示 23:28
   （还在未来 78 分钟）却仍报 TOKEN_EXPIRED。
   正确签名算法（实测通过，appKey=34839810）：
   ```
   token  = _m_h5_tk.split('_')[0]
   sign   = md5(f"{token}&{t}&{appKey}&{data}")
   t      = str(int(time.time() * 1000))
   data   = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
   POST https://h5api.m.goofish.com/h5/mtop.taobao.idle.user.get/1.0/
        ?jsv=2.7.2&appKey=34839810&t={t}&sign={sign}
   ```
   服务端会在 `Set-Cookie` 里回一个新的 `_m_h5_tk` + `_m_h5_tk_enc`，
   需要保存这对**配套**的新值。

## Token 自愈机制（生产已验证）

**文件**：`src/xianyu_session.py`

**核心逻辑**：
- 启动时 `sync_server_token()`：用 `mtop.taobao.idle.user.get` 触发一次握手，拿到服务端最新 `_m_h5_tk`/`_m_h5_tk_enc` 配套对
- 所有搜索请求走 `call_with_token_refresh()` 包装：
  - 捕获 `FAIL_SYS_TOKEN_EXOIRED` / `FAIL_SYS_TOKEN_ILLEGAL` / `FAIL_SYS_TOKEN_EMPTY` / `XianyuConfigError`(token 缺失)
  - 自动重新握手一次，再重试原请求
- **仅作用 Phase 1**（Phase 2/3/4 由 goofish-cli 内部鉴权）
- **登录态失效 (`SESSION_EXPIRED`) 不可自愈**，必须重导 Cookie

**占位兜底**：首次握手前若 `_m_h5_tk` 为空，注入占位 hex token（md5+timestamp）触发握手，防止 `XianyuConfigError`。

**验证日志**：`检测到令牌问题, 已对齐服务器令牌` -> Phase 1 稳产 21+ 信号/页。

## 读平台数据（商品指标 / 客询会话）—— 走 pyxianyu 自愈路径，别走 goofish MCP

**做销售诊断必须能读回平台数据。四条路径实测对照（2026-10-18）：**

| 路径 | 结果 |
|---|---|
| `goofish` CLI **裸跑** | ✗ `FAIL_SYS_SESSION_EXPIRED` ← **假阴性**！进程环境里没有 cookie |
| `goofish` **MCP**（带 cookie） | ✗ `FAIL_SYS_TOKEN_EXOIRED` ← 真错：**这条路没有令牌自愈** |
| 图片上传子域 | ✅ HTTP 200（证明 cookie 本身是好的）|
| **pyxianyu + `sync_server_token`** | ✅ **成功读回** |

⇒ **读数据一律走 pyxianyu，每次调用前 `sync_server_token(client)`**（清 host-only `_m_h5_tk`）。
goofish-cli / MCP 那条路缺清理逻辑，读接口注定报令牌过期。

### ★ 商品状态语义（最容易搞错的地方，必读）

**`itemStatus` 的数字含义与直觉相反：**

| `itemStatus` | 含义 |
|---|---|
| **`0`** | **在售** |
| **`1`** | **非在售**（平台归入「已售出」组）|

**权威判据 —— 不要猜，直接读平台自己给的定义：**

```python
r = api.get_all_user_items(uid, 20)
for g in r["itemGroupList"]:
    print(g["groupName"], g["itemNumber"], g["searchCondition"])
# 实测输出：
#   综合   40  []
#   在售    2  [{'status': '0'}]     ← status='0' 就是在售
#   已售出 38  [{'status': '1'}]
```

⇒ **`itemGroupList[].searchCondition` 是平台给出的状态定义，比任何猜测都可靠。**
自己仓库的生产代码往往也写了同一件事（`item_manager.py` 里的
`... in ("在售","在线","selling","0")`）—— 读代码要认真。

**`get_all_user_items` 的几个要点**
- 它**会遍历分组翻页**（`selected_group = itemGroupList[0]`），所以裸调
  `get_user_items(page_number=1)` 可能返回空 —— 要状态就用 `get_all_user_items`
- 返回里有 `itemGroupList`（分组+数量+筛选条件）、`cardList`、`pageCount`；
  `totalCount` 实测恒为 0，**别拿它当总数**，要用 `综合` 组的 `itemNumber`
- 列表层 `cardData.itemStatus` 就是状态，**不需要**逐条调详情接口（详情还会撞风控）

**⚠️ 做销售诊断前的第一性原则**：先确认「在售」集合，再谈客询/成交。
在非在售商品上算客询率/成交率毫无意义 —— 它们本来就不会成交。
**在售件数很少时（如 n=2）不要算任何“率”**，统计上无意义。

### 商品侧

```python
uid = parse_cookie(ck).get("unb")          # 卖家 user_id 就是 cookie 里的 unb
r = call_with_token_refresh(client, api.get_all_user_items, uid, 20)
items = r["cardList"]                      # 每项 = {cardData:{...}, cardType}
# 指标藏在 get_item_info(item_id) 里：
#   浏览 data.b2cItemDO.browseCnt          ← 平台不对卖家暴露，实测恒为 0
#   想要 data.itemDO.wantCnt               ← 最接近客询意愿的代理指标
#   成交 data.itemDO.soldCnt
#   账号级：data.sellerDO.hasSoldNumInteger（历史总成交）
```

### 客询会话（`客询率` 的数据源）★

`pyxianyu` **没有**消息接口（`pyxianyu.message` 只是内容类型）。但 `XianyuClient`
暴露了 mtop 原语（`build_mtop_params` / `post_json` / `parse_json_response` /
`ensure_api_success`），**可以自拼任意 mtop 端点**：

```python
URL = "https://h5api.m.goofish.com/h5/mtop.taobao.idlemessage.pc.session.sync/3.0/"
params = client.build_mtop_params(api="mtop.taobao.idlemessage.pc.session.sync",
                                  spm_cnt="a21ybx.im.0.0", spm_pre="a21ybx.im.0.0",
                                  log_id="xianyu_im", v="3.0")     # ← version 必须 3.0
resp = client.post_json(URL, params=params,
                        data_val=json.dumps({"fetchNum": 50}))   # ← 参数名 fetchNum
sessions = client.ensure_api_success(
    client.parse_json_response(resp, api_name=API), api_name=API)["data"]["sessions"]
```

**字段坑（都会静默给 None）**
- 未读数在 **`message.summary.unread`** —— 不是 `unreadCount`，也不是 `message.unread`
- 时间在 `message.summary.ts`（**可能是毫秒**，>10¹² 就 //1000）
- 对方身份在 `session.ownerInfo.userId` / `.nick`

**踩过的错**：先猜 `version="1.0"` → `FAIL_SYS_API_NOT_FOUNDED::请求API不存在`。
⇒ **接口参数不要猜，去读现成实现**：`goofish_cli/commands/message/list_chats.py`
（`venv/Lib/site-packages/` 下，pip 包自带源码）—— 比猜快得多且不会错。

**速率限制**：连续读接口会撞 `FAIL_SYS_USER_VALIDATE`（风控）。实测 40 条商品里
第 32-40 条被拦。⇒ 逐条读要加间隔（≥0.8s）并做退避重试。

> 探针脚本参考：`xiangmu/xianyu_agent_workflow/tools/` 下
> `collect_r6_metrics.py`（商品指标）、`probe_r6_sessions.py`（客询会话）

## 指标可得性矩阵（2026-10-18 实测，别再重探）

做销售诊断/定价前先看这张表。四条探测卡（00-接口清单 / 01a 在售清单 / 01b 流量 / 01c 交易）交叉验证后的定论。方法论见 `platform-metrics-availability-probe`。

| 指标 | 结论 | 依据 |
|---|---|---|
| 商品列表 / 标题 / 价格 / 状态 / 图 / 标签 | ✅ 可得 | `goofish item list`；**`--limit` 硬夹 100**（`list.py:12,22`）|
| 浏览 / 想要 / 收藏 / 成交 | ⚠️ 有时可得 | `mtop.taobao.idle.pc.detail` 唯一来源；先打一次 `item list` 续期令牌；**会被 RGV587 风控** |
| 曝光量 | ❌ 平台不存在该字段 | itemDO 62/60 字段全扫，`exposureCnt/exposCnt/showCnt/pvCnt/uvCnt/impressionCnt/viewCnt/visitCnt` 全 False；含 cnt 的只有 7 个：browseCnt/collectCnt/favorCnt/interactFavorCnt/soldCnt/wantCnt/wantCntUnit |
| 成交额 GMV | ❌ 接口永久不存在 | 17 个 CLI 命令 0 命中；goofish-cli 9 + pyxianyu 11 个 mtop API 无 order/trade；`order list` → `No such command` |
| 询单数（商品维度） | ❌ CLI 自己丢字段 | `commands/message/list_chats.py:38` 的 `_parse_session()` 把 `item_id` 硬编码空串（只有 `--watch-secs>0` 的 WS 行才回填）→ 绕过 CLI 直读 raw 才有 |
| 询单数（会话维度） | ✅ 可得 | `session.sync`（v=3.0, `fetchNum`）全量 40 条、`hasMore=false`；按 `session.itemInfo.itemId` 聚合 |
| 上架时间 | ✅ 可得 | `itemDO.gmtCreate`（曾误判不可得，已在 §勘误 修正）|

**两个口径陷阱（都会静默给 0）**
1. **`soldPrice` 不是成交额** —— `core/item_data.py:21` 把它映射成 `normalized.price`（挂牌价，与 `priceInfo.price` 完全相同）。拿它乘 `soldCnt` 永远得 0。
2. **`ItemManager.list_items` 失败时静默 `return []`**（`item_manager.py:115-117`），与「0 件商品」不可区分。判定在售集合前先 grep 日志里的 `ERROR item_list 失败`。

**`_m_h5_tk` 过期 ≠ 登录态失效（这条推翻了长期误解）**

服务端在响应 `Set-Cookie` 里当场下发新令牌 —— **重试一次就成功**，不需要 Playwright：
```
[before] _m_h5_tk 到期=2026-10-15 21:40:43 EXPIRED
首次调用 → AuthRequiredError: FAIL_SYS_TOKEN_EXOIRED
[after]  _m_h5_tk domain=.goofish.com 到期=2026-10-18 05:46:10 FRESH
重试 → SUCCESS cardList len=20
```
但 `core/mtop.py:118-137` 在令牌过期时**直接跳 Playwright**，跳过了「用续期令牌重试一次」，所以 CLI 单次命令永远 `exit 77`。而 Playwright 自愈实测 3 次全失败（`core/browser.py` 每次 `mkdtemp()` 起空 profile，没有免密记忆，「快速进入」必然 `Frame was detached`），**cookies.json mtime 全程未变**。⇒ 想读数据不要指望自愈：用 pyxianyu 的 `sync_server_token` + 自建重试，或直接调 raw。（框架源码级修法：令牌层先重试一次，再考虑 Playwright。）

**同名 cookie 域冲突**：`cookies.json` 扁平导入的 `domain=''` 与服务器下发的 `.goofish.com` 会并存同名 `_m_h5_tk`，`requests` 抛 `CookieConflictError` — 必须先按 `(name, domain, path)` 清旧项再重试。

**`item view` 走浏览器路径**：实测 3 次全失败，报 `Page.evaluate: Execution context was destroyed, most likely because of a navigation`。官方 `_bundled_skills` 说 item_view 能看曝光，实际 `view.py:112-114` 只映射 want/collect/browse —— 照那份文档写归因就是编数据。

**CLI 入口别搞错**：命令行是 `goofish.exe`（`goofish list-commands --format json` 有 `write` 字段：13 只读 / 4 写 = item publish、item delete、media upload、message send）；`goofish-cli` 本身是 MCP stdio server。`grep -rn "XIANYU_COOKIE" goofish_cli/` 命中 **0** —— 框架 `mcp_config.json` 里那段是死配置，真登录态只在 `~/.goofish-cli/cookies.json`（可用 `GOOFISH_COOKIES_PATH` 换路径）。

## Phase 3 自动上架 —— item_id 解析修复（关键）

**问题**：`mcp_tools.call_tool` 返回完整 MCP result 对象，`item_id` 嵌套在：
1. `structuredContent.data.item_id`（优先，goofish-cli 新版）
2. `content[0].text` -> JSON -> `data.item_id`（旧版）
3. 直接 `data.item_id`（兜底）

**原代码只读 `result.data.get("item_id")` 导致全部为空，上架 0 个**。

**修复**（`phase3_lister.py:publish_task`）：
```python
if result.success:
    item_id = ""
    data = result.data
    if isinstance(data, dict):
        # 优先：structuredContent.data.item_id
        structured = data.get("structuredContent", {})
        if isinstance(structured, dict):
            inner = structured.get("data", {})
            if isinstance(inner, dict):
                item_id = inner.get("item_id", inner.get("itemId", ""))
        # 次选：content[0].text -> JSON -> data.item_id
        if not item_id:
            content = data.get("content", [])
            if content and isinstance(content, list):
                text = content[0].get("text", "")
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        inner = parsed.get("data", parsed)
                        if isinstance(inner, dict):
                            item_id = inner.get("item_id", inner.get("itemId", ""))
                except json.JSONDecodeError:
                    pass
        # 兜底：直接在 data 里
        if not item_id:
            item_id = data.get("item_id", data.get("itemId", ""))
    
    if item_id:
        task.item_id = item_id
        task.status = "success"
        ...
```

**验证**：实测后 Phase 3 能正确拿到 `item_id` 并标记 success。

## 百度网盘 errno=115 —— 账号级限制，换官方 OAuth 通道（已实测）

**先分清**：`errno=115` 读 `show_msg` 字段（不是 `errmsg`）。
若 `show_msg` 含「账号异常」「禁止分享」→ **账号级限制，重试 100 次也没用**，
fail-fast 并改用官方通道（见 `references/bdpan-official-channel.md`）。
只有非「账号异常」的 115（已分享/频控）才值得重试。

**官方通道实测**：上传 ✅ `code:0`；分享 ✅ 返回 link+pwd（**无** errno=115）。
Phase 2.5 从 `{'failed': 2}` → `{'published': 2}`。
后端开关：`NETDISK_BACKEND=bdpan|baidu`（默认官方优先自动回退）。

> 详细：`references/bdpan-official-channel.md`
> （安装、OOB 登录、Python 封装 `src/netdisk_bdpan.py`、作用域/路径规则、坑）

## 商品素材质量：封面 + 文案（必读）

**文案不能写成合规文档** —— 不要开头「【这份资料我做了什么】」、不要列内部文件名
（`00-内容总览.md`/`PROVENANCE.json`）、不要引法条编号。
要 emoji 分区、**利益点开头**、把内部实现翻译成买家利益。
法条存 `LEGAL_BASIS` 常量，正文只写「数字商品发出后不支持无理由退款」。

**封面用 Playwright + HTML/CSS，不用扩散模型** —— 生图模型中文常乱码，
而「78份」「永久有效」必须字字准确。2x device_scale_factor 出 1600px。

> 详细：`references/copy-and-cover-quality.md`
> （竞品对照、写作规则、翻译示例、封面排版公式、MCP 客户端两个硬伤）

**MCP 客户端硬伤（会静默吞掉失败，必查）**：
1. 只判 `isError` 会漏掉 `structuredContent.ok=false` → 限流重试被跳过
2. StreamReader 默认 64KB → 长简介报 `LimitOverrunError`

## 闲鱼登录态：三层坑（已全部实测解开）

1. **`browser_cookie3.firefox()` 读的是错的 profile** —— 多 profile 时它只读
   `profiles.ini` 的 default，可能已发霉数月。必须扫所有 profile 按
   `cookies.sqlite` mtime 取最新。
2. **`cookie2` / `_tb_token_` 在磁盘上取不到** —— 是会话 cookie（`Max-Age=-1`），
   Firefox 不落盘、requests 直接删。解法：**真浏览器访问 `/bought` 强鉴权页
   触发服务端下发**（不需要 passport「快速进入」）。
3. **`auth_status` 会假阴性** —— `valid:false` 但 `item_list` 正常。
   预检必须用**真实业务调用**判断。

**上架报「类目推荐响应缺少选中分类身份」** → 封面是占位图，AI 类目推荐对自造词
无效 → 必须用**实测兜底 DTO**（`FALLBACK_CATEGORY`）并作为 `category` 传给
`item_publish`，让 goofish-cli 跳过内部 recommend。

> 详细：`references/session-and-category-recovery.md`
> （完整解法、刷新/导入脚本、预检三项、发布成功链路、关键教训）

**调度顺序（`run_daily.bat`）**：
`同步 cookie → 浏览器刷新会话 → 导入 goofish-cli → 预检 → 跑流水线`

**⚠️ 纠正上一版**：此处**不都是**可重试的 115；缺会话令牌也别只怪 token 过期。

## tar symlink 过滤（避免解包报错）

**问题**：`simple-icons` 等仓库含 `.nvmrc` symlink，原代码 `raise PublishError` 中止**整包**。

**修复**（`src/factory_publish.py:_safe_extract_tar`）——**跳过**链接成员而非中止整包：
```python
safe_members = []
with tarfile.open(tar_path, "r:gz") as tf:
    for m in tf.getmembers():
        if m.name.startswith("/") or ".." in Path(m.name).parts:
            raise PublishError(f"tar 成员路径越界，拒绝解包: {m.name}")
        if m.issym() or m.islnk():
            logger.warning(f"tar 含链接成员，跳过: {m.name}")
            continue                      # 跳过，不中止
        target = (dest / m.name).resolve()
        if not str(target).startswith(str(dest)):
            raise PublishError(f"tar 成员解析后越界: {m.name}")
        safe_members.append(m)
    tf.extractall(dest, members=safe_members)   # 只解包安全成员
```

> `filter='data'` (Py3.12+) 更简洁，但本项目用的显式 `members=` 白名单已验证可用。
> **不要**因为一个 symlink 就放弃整个仓库 —— 那些链接多半是 `.nvmrc` 之类无害文件。

## Chrome 安装到 D: 盘（directory junction 方案）

**约束**：Chrome 无自定义安装路径选项；goofish-cli `core/browser.py` **硬编码** `channel="chrome"`，只认 `%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe`。

**方案**：
1. 下载官方离线安装包 `ChromeStandaloneSetup64.exe` (160MB)
2. 剥离嵌套 7z：SFX -> outer 7z -> updater.7z -> chrome_installer.exe -> inner 7z -> `chrome.7z` (491MB) -> 标准 `Application/` 目录结构
3. 物理放置 `D:\Ai\Google\Chrome\Application\chrome.exe`
4. 创建 junction：`C:\Users\Administrator\AppData\Local\Google\Chrome ==> D:\Ai\Google\Chrome`
   - PowerShell: `New-Item -ItemType Junction -Path "$src" -Target "$dst"`
   - **mklink 是 cmd 内建，PowerShell 必须用 New-Item**

**验证**：Playwright `channel="chrome"` 解析到 D: 实体；goofish-cli `goofish_page()` 启动加载闲鱼首页；`core/refresh.py` 登录态自愈机制跑通。

## 上线前预检（preflight）—— 别白跑 20 分钟

**教训**：整条流水线要跑 15-25 分钟。若账号层面就没戏（登录失效 / 网盘禁分享），
跑完才发现 Phase 3 上架 0 个，纯浪费。**先预检，10 秒内退出。**

`scripts/preflight_check.py` 检查两个硬前提：
1. **闲鱼登录态**：`auth_status` → `structuredContent.data.valid`
   - ❌ `FAIL_SYS_SESSION_EXPIRED::Session过期` → 上传/发布必失败
   - **注意登录态解析路径**：`structuredContent.data.valid`（不是 `structuredContent.valid`）
2. **网盘分享能力**：用**真实 fs_id** 试 `share/set`，读 `show_msg` 认「账号异常」

```python
# run_daily.bat 集成：预检失败 exit 2 跳过流水线
"%PYTHON%" scripts\preflight_check.py > "%LOG_DIR%\preflight.log" 2>&1
if errorlevel 2 ( echo PREFLIGHT FAILED >> log & exit /b 2 )
```

## 闲鱼登录态 = Phase 3 的总开关（最大坑）

**症状**：Phase 1 搜索正常（21-73 信号），但 Phase 3 全部「图片上传失败」→「上架 0 个」。

**根因（HTTP 直测拿到）**：
```
POST stream-upload.goofish.com/api/upload.api →
HTTP 302 → market.m.taobao.com/app/idleFish-F2e/fish-pc/login.html
响应头 s_status = STATUS_NOT_EXISTED
```
- **搜索不需要登录**（匿名 mtop token 自愈即可）→ Phase 1 正常
- **上传/发布必须登录** → 登录失效则 Phase 3 必然全灭
- `goofish auth status` 的 `valid: false` 是最终判决

**登录态失效不可自愈**。goofish-cli 的 Playwright「快速进入」免密刷新也救不了
（实测 `Locator.click Timeout 5000ms` + 「拿到 0 个 cookie」）。
**唯一解**：在浏览器重新登录 → 重新导出 cookie。

## Firefox Cookie 同步（自动化，含 preflight 前置）

`scripts/sync_cookie_from_firefox.py` —— 从 Firefox 读 goofish.com cookie 写入 `.env`：
```python
import browser_cookie3
cj = browser_cookie3.firefox(domain_name="goofish.com")
cookie = "; ".join(f"{c.name}={c.value}" for c in cj if "goofish" in (c.domain or ""))
# 关键字段校验：unb / _m_h5_tk / _m_h5_tk_enc / cna
```
**为什么必须有 `unb`**：goofish-cli 的 `auth_login` 会校验 `unb` + `_m_h5_tk`；
旧 `.env` 静态 cookie 常缺 `unb` → 报「cookie 缺失关键字段 unb / _m_h5_tk」。

**集成**：`run_daily.bat` 在跑流水线**之前**先执行 cookie 同步，再跑 preflight。

**已实测**：`browser_cookie3.firefox(domain_name='goofish.com')` 读取 18 个字段，
含 `unb` / `_m_h5_tk` / `_m_h5_tk_enc` / `cna`。

**区分「token 过期」与「登录态过期」**：
- `_m_h5_tk` 轮换/过期 → **可自愈**（Phase 1 token 自愈机制）
- `SESSION_EXPIRED`（unb 无会话）→ **不可自愈**，必须重登

## Windows Task Scheduler 自愈注册模式

**问题**：`schtasks /create` / `Register-ScheduledTask` 在非管理员 shell 返回 `HRESULT 0x80070005`。

**模式**：
```bat
REM register_tasks_admin.bat - 自愈提权
@echo off
net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
REM ... 真正的注册逻辑 ...
schtasks /create /tn "XianyuPipeline-Daily" /tr "..." /sc daily /st 02:30 /ru "SYSTEM" /rl highest /f
```

**关键规则**：`.bat` 文件必须纯 ASCII（cmd 读 GBK 会乱码中文注释）；用 `New-Item -ItemType Junction` 而非 `mklink`。

## C: 盘清理已验证安全路径

| 路径 | 大小 | 处理方式 |
|------|------|----------|
| `C:\Users\<user>\AppData\Local\npm-cache` | 1.15GB | `npm cache clean --force` (自动重建) |
| `C:\Users\<user>\AppData\Local\pip\cache` | ~500MB | `pip cache purge` |
| `C:\Users\<user>\AppData\Local\Doubao\update_data` | 1.73GB | 迁移到 `D:\Ai\AppData\Doubao` + junction |
| `C:\Users\<user>\AppData\Roaming\coze` | 2.61GB | 迁移到 `D:\Ai\AppData\coze` + junction |
| `C:\Users\<user>\AppData\Local\Thunder Network` | 0.94GB | 迁移到 `D:\Ai\AppData\ThunderNetwork` + junction |
| `C:\Windows\Installer` | ~8GB | **不动**（系统组件修复需） |
| `C:\Program Files\WSL` | ~2GB | **不动**（WSL2 运行时） |

**结果**：2.41GB -> 9.08GB (释放 6.68GB)，后续迁移 Doubao/coze/Thunder 再释放 10GB+，**总计 2.4GB -> 18.4GB**。

## 调试日志规范（项目根目录维护 DEBUG_LOG.md）

| 字段 | 内容 |
|------|------|
| 问题 | 现象描述 |
| 方案 | 修复思路 |
| 文件 | 修改文件路径 + 行号 |
| 验证 | 单测/实测命令 + 通过标准 |

**回归测试记录表**：**修复前/后同跑全链路，零回归才算过**。

## 参考文件
- `references/pyxianyu-api.md` - pyxianyu 核心 API 速查
- `references/cookie-format.md` - Cookie 字段详解
- `references/token-and-auth.md` - token 自愈、goofish-cli 登录态、MCP 认证流
- `references/project-structure.md` - 项目目录、入口命令、环境变量、定时器部署
- `references/compliance-gate.md` - 合规自检规则、标题模板、敏感词映射
- `references/sales-diagnostics.md` - 销售监控字段、诊断规则表、反向优化动作
- `references/hard-timeout.md` - 硬超时配置表、注入位置、Phase4 看门狗
- `references/netdisk-baidu.md` - 百度网盘 PCS API、errno=115 账号级限制判定（读 `show_msg`）、分享链接生成
- `references/chrome-on-d.md` - Chrome D 盘安装、junction、Playwright channel 解析
- `templates/.env.example` - 完整环境变量模板
- `scripts/parse_cookie.py` - Cookie 字符串<->dict 转换工具
- `scripts/register_tasks_admin.bat` - 自愈提权 Task Scheduler 注册
- `scripts/install_chrome_to_D.bat` - Chrome D 盘安装器（自愈提权）

模板化标题/文案里的「999套」「888份」若为随机生成 = **虚假宣传**（违法）。
正确做法：
- 标题/文案中的 `{count}` **只能填真实统计**（如真实文件数）
- 拿不到真实数量 → 用不含数字的写法（「整套」「全套」）
- 品类没有专属文案时**不要套用其他品类文案**（内容不符也是虚假描述）

## 合规自检（已落地硬性机制）
`src/listing_copy.py` 内置 `validate_no_false_claims()`，**发布前强制拦截**：
- 中文数字（一百、两千）⛔
- 带逗号数字（1,000、888）⛔
- 全角数字（１２３）⛔
- 页数/大小/时长等具体数字不在 `verified` 集合内 ⛔
- 仅允许 `deliverable_manifest.delivery.file_count` 透传的真实数量 ✅

**标题示例**（来自真实 file_count）：
```
Excel表格资料包78份最新202610版
速查表合集62日常办公适用
设计工具合集127效率提升适用
```
## 定时自动化（生产环境）
### systemd user timer 方案（推荐）
每天 02:30 自动跑完整流水线 Phase 1-3：
```bash
# ~/.config/systemd/user/xianyu-pipeline.service
[Unit]
Description=Xianyu Daily Full Pipeline (Phase 1-3)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/home/user01/.hermes/python/xianyu_pipeline
Environment=PATH=/home/user01/.hermes/python/xianyu_pipeline/.venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=XIANYU_COOKIE=${XIANYU_COOKIE}
Environment=BAIDU_BDUSS=${BAIDU_BDUSS}
Environment=OPENAI_API_KEY=${OPENAI_API_KEY}
ExecStart=/home/user01/.hermes/python/xianyu_pipeline/.venv/bin/python main.py run --pages 3 --limit 10 --listing-mode api
StandardOutput=append:/home/user01/.hermes/python/xianyu_pipeline/logs/daily_pipeline.log
StandardError=append:/home/user01/.hermes/python/xianyu_pipeline/logs/daily_pipeline.err.log

# ~/.config/systemd/user/xianyu-pipeline.timer
[Unit]
Description=Run Xianyu pipeline daily at 02:30

[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true
RandomizedDelaySec=15m

[Install]
WantedBy=timers.target
```

启用：
```bash
systemctl --user daemon-reload
systemctl --user enable --now xianyu-pipeline.timer
systemctl --user status xianyu-pipeline.timer
```

### Windows Task Scheduler 方案 (Windows 原生，无 WSL2)
每天 02:30 自动跑完整流水线 Phase 1-3，使用 SYSTEM 账号最高权限：
```bat
REM D:\Ai\Agent\xiangmu\run_xianyu_pipeline.bat
@echo off
set PROJECT_DIR=D:\Ai\Agent\xiangmu\xianyu_pipeline
set VENV_DIR=%PROJECT_DIR%\venv
set LOG_DIR=%PROJECT_DIR%\logs
if exist "%VENV_DIR%\Scripts\python.exe" set PYTHON=%VENV_DIR%\Scripts\python.exe
for /f "usebackq delims=" %%a in (`type "%PROJECT_DIR%\config\.env" ^| findstr /v /r /c:"^#" /c:"^$"`) do set "%%a"
cd /d %PROJECT_DIR%
%PYTHON% main.py run --pages 3 --limit 10 --listing-mode api ^
    >> %LOG_DIR%\daily_pipeline.log 2>> %LOG_DIR%\daily_pipeline.err.log
```

注册定时任务 (需管理员权限)：
```bat
REM D:\Ai\Agent\xiangmu\register_task_admin.bat
schtasks /create /tn "XianyuPipeline" /tr "D:\Ai\Agent\xiangmu\run_xianyu_pipeline.bat" /sc daily /st 02:30 /ru "SYSTEM" /rl highest /f
```

**Key rule**: Never run `schtasks /create` or `Register-ScheduledTask` from non-elevated shell — they fail with `HRESULT 0x80070005`. Always right-click the `.bat` → **以管理员身份运行**.

### 销售监控 + 诊断反向优化（闭环设计）
**新增两个模块**（待落地）：
1. `src/sales_monitor.py` - 复用 goofish-cli MCP，定时拉取「我的商品」列表，解析 `want_count`/`view_count`/`sold_count`/`status`，追加写入 `data/sales_history.jsonl`
2. `src/diagnostics.py` - 读取销售历史 + 上架参数，规则引擎判定滞销原因，输出 `output/diagnostics/diagnosis_YYYYMMDD.json`，下一轮 `run` 自动应用建议（重发/改价/优化文案）

**诊断规则表**：
| 指标 | 滞销判定阈值 | 可能原因 | 自动建议动作 |
|------|--------------|----------|--------------|
| `sold==0` 且 `view<50` (3天) | 曝光不足 | 标题关键词弱/类目错/主图差 | 换标题模板、换类目、重做主图、降价 10% |
| `want/view < 0.02` | 点击想要率低 | 价格高/文案不痛点 | 降价、换 SKU 结构、加「限时」文案 |
| `sold>0` 但 `rating<4.5` | 交付/质量问题 | 网盘链接失效/资料不全 | 检查发货链接、补齐资料、主动好评 |
| 同类目竞品 `price < me*0.8` | 价格无竞争力 | 定价策略偏高 | 动态降价至竞品中位数 |

## 调试日志规范
项目根目录维护 `DEBUG_LOG.md`，**每次修改必记录**：
| 字段 | 内容 |
|------|------|
| 问题 | 现象描述 |
| 方案 | 修复思路 |
| 文件 | 修改文件路径 + 行号 |
| 验证 | 单测/实测命令 + 通过标准 |

回归测试记录表：**修复前/后同跑 141 单测，零回归才算过**。

## 参考文件
- `references/pyxianyu-api.md` - pyxianyu 核心 API 速查
- `references/cookie-format.md` - Cookie 字段详解
- `references/project-structure.md` - 项目目录、入口命令、环境变量、定时器部署
- `references/compliance-gate.md` - 合规自检规则、标题模板、敏感词映射
- `references/sales-diagnostics.md` - 销售监控字段、诊断规则表、反向优化动作
- `templates/.env.example` - 完整环境变量模板
- `scripts/parse_cookie.py` - Cookie 字符串<->dict 转换工具
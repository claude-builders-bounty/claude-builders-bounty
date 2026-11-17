---
name: xianyu-demand-scan
version: "1.0.0"
description: 用闲鱼真实在售数据做需求/定价扫描：按关键词拉取商品标题、价格、地区、卖家、想要标签，输出 CSV 与价格带统计（P50/P75/引流价占比/卖家密度）。当用户问「闲鱼上 X 好不好做/该卖多少钱/有没有需求」时使用。
tags: [xianyu, demand-research, pricing, goofish, ecommerce]
---

# 闲鱼需求扫描（xianyu-demand-scan）

## 何时用
- 用户问某个品类/服务在闲鱼「有没有需求、卷不卷、该定价多少」
- 需要为新品/新服务找价格锚点（P50/P75）和供给缺口
- 要对比多个关键词的供给密度与价格带

## 何时不用
- 需要真实成交额/销量：搜索接口不提供，得另调详情接口（见「已知缺口」）
- 要做铺货/上架/发货自动化：那是 `xianyu-automation` / `automated-virtual-goods-pipeline`，不要混用

## 前置条件（必须逐条确认）
1. **Cookie**：优先环境变量 `XIANYU_COOKIE`；否则读 `D:\Ai\Agent\xiangmu\xianyu_pipeline\config\.env`。
2. **Python 环境**：管线的 `venv` 已损坏（pyvenv.cfg 指向不存在的豆包沙箱 python），**不要试图修复或重建**。
   正确姿势是用系统 Python + 该 venv 的 site-packages：
   ```
   PYTHONPATH = D:\Ai\Agent\xiangmu\xianyu_pipeline\venv\Lib\site-packages;D:\Ai\Agent\xiangmu\xianyu_pipeline
   ```
   `scripts/run.ps1` 已经封装好，直接调它。
3. **令牌**：pyxianyu 首次调用常报 `FAIL_SYS_TOKEN_EXOIRED`，`call_with_token_refresh` 会自动对齐服务器令牌并重试，属正常，不要当失败。

## 用法
```powershell
# 单个关键词（30 条/页）
powershell -NoProfile -File D:\Ai\.dsh\skills\xianyu-demand-scan\scripts\run.ps1 "本地大模型部署"

# 多关键词
... run.ps1 "ComfyUI部署" "本地大模型部署" "Ollama安装"

# 直接跑 python（自定义页数/输出目录）
python scripts/scan.py --pages 2 --out D:\Ai\xianyu-demand\out "关键词"
```

输出：
- `<out>\scan.csv`（UTF-8 BOM，Excel 可直接开）
- `<out>\scan.json`
- stdout 汇总：每个关键词的 n、卖家数、min/P50/P75/max、引流价条数、带原价标签数、带想要数

## 详情补充（匿名，零账号风险）
搜索只给标题/价格，**想要数、浏览量、收藏数必须调详情接口**。好消息：详情接口**不带任何 Cookie 也能用**（已实测 30/30 成功）。

```powershell
python scripts/detail.py --from-scan D:\Ai\xianyu-demand\out\scan.json --sleep 2.5
```

输出 `details.csv/json`，字段：want（人想要）、browse（浏览量）、collect（收藏）、sold（成交数）、price、created、status。
- 实测：30 条服务中 25 条有想要数；`sold` 全为 0，**该字段对服务/虚拟品不可靠，别拿它证明没成交**。
- 匿名调用也要节流（默认 2.0–2.5s），但不是账号风险。

## 风控策略（用户红线：宁可慢，不许封号）
| 动作 | 是否碰账号 | 频率上限 | 说明 |
|---|---|---|---|
| 关键词搜索 | **是**（需 Cookie） | 每次 ≤3 个关键词，间隔 ≥6s | 唯一有风险的环节；匿名搜索实测报 `RGV587` 不可用 |
| 商品详情 | 否（匿名） | 2–3s/条 | 30 条约 1.5 分钟，安全 |
| 上架/改价/下单 | 是 | 不在本技能范围 | 用 xianyu-automation，风险另算 |

出现 `FAIL_SYS_USER_VALIDATE` 或 `RGV587`：立即停止搜索，隔 24h 再试，或换 `XIANYU_COOKIE` 小号。

## 数据口径与坑（照抄，别重新踩）
| 现象 | 真相 | 处理 |
|---|---|---|
| 价格显示 ¥1、¥0.1 | 引流价，不是真实报价 | 取 `real_price`（tags 里 labelId=41 的划线价）；没有就标注「仅引流价」 |
| 想要数全是 0 | 搜索接口对多数条目**不下发** `want` 标签，不是真没人想要 | 禁止用「想要=0」论证需求弱；要需求强度必须逐条调详情接口 |
| 标题 120 字截断 | 脚本按 120 字截断存 CSV | 需要全文就改 `title[:120]` |
| `FAIL_SYS_USER_VALIDATE` | 账号被风控挑战 | 立即停手，降频/换号，别硬刚 |
| 同一卖家刷屏 | 供给密度做假 | 统计时按 `seller` 去重看真实供给方数量 |

## 分析口径（写结论必须带这些数）
1. **价格带**：P50 = 市场心理价，P75 = 高价带门槛；用 `real_price`，没有才退回展示价并注明。
2. **供给密度**：n 与去重卖家数。卖家数 ≈ n 且价格拥挤 → 红海；卖家少但价格跨度大 → 有分层。
3. **引流占比**：display_price ≤ 2 的比例。>30% 说明该词已被 ¥1 引流号占领，正面拼价必输。
4. **缺口判断**：只有「P75 以上条数 ≤ 3 且存在 ≥P50 的真实成交迹象」才算高价缺口；n < 10 一律标「样本不足」。
5. **结论必须挂数字**：至少给出 n、卖家数、P50、P75、引流占比，禁止「感觉挺卷」。

## 报告模板
```
## 关键词：<kw>
- 样本：n=<n>，去重卖家 <m>，采集时间 <ts>
- 价格：min <..> / P50 <..> / P75 <..> / max <..>（口径：real_price，缺失 N 条）
- 引流价（≤¥2）：<k> 条（<pct>%）
- 缺口判断：<有/无>，依据：<具体条数与价格>
- 建议定价：<¥x–y>，理由：<对标哪几条>
- 风险：<风控/引流/同质化>
```

## 合规与账号安全
- 只读接口，禁止用于上架/改价/下单；不要高频循环（脚本默认 1.5s/关键词）。
- 用主号前先提醒用户风控风险；建议小号采集、主号只挂服务。
- Cookie 只从 env 或本地 .env 读，**绝不写进报告、日志、git**。
- 已知泄漏点：`xianyu_pipeline/src/phase1_selector.py` 里硬编码过 NVIDIA key，不要复制该文件里的任何密钥。

## 排查
| 报错 | 原因 | 动作 |
|---|---|---|
| `ModuleNotFoundError: pyxianyu` | 没设 PYTHONPATH | 用 `run.ps1`，别直接 `python scan.py` |
| `FAIL_SYS_TOKEN_EXOIRED` 重试 3 次仍失败 | Cookie 过期 | 让用户重新导出 goofish.com 的完整 Cookie |
| `FAIL_SYS_USER_VALIDATE` | 风控 | 停止采集，换号或隔天 |
| 价格全为空 | 该搜索页只有图文流/广告位 | 换关键词或加 `--pages 2` |

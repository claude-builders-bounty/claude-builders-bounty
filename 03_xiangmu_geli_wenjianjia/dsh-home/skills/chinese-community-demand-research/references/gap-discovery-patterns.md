# Gap Discovery Patterns — Finding True Underserved Demand

## Core Gap Search Patterns (Baidu `site:tieba.baidu.com`)

### Generic "Nobody Built This" Patterns
```bash
# Explicit absence language
site:tieba.baidu.com ("没人做" OR "没人开发" OR "没人搞" OR "空白" OR "缺失") ("工具" OR "软件" OR "开源")
site:tieba.baidu.com ("求开发" OR "求大佬做" OR "悬赏开发" OR "有偿开发") ("工具" OR "脚本" OR "程序")
site:tieba.baidu.com ("急需" OR "迫切需要" OR "强烈需求") ("没有" OR "缺") ("工具" OR "方案")
site:tieba.baidu.com ("冷门" OR "小众" OR "非主流") ("需求" OR "痛点") ("开源" OR "工具")
site:tieba.baidu.com ("全网找不到" OR "GitHub上没有" OR "开源界空白")
```

### Domain-Specific Gap Patterns (Validated This Session)

#### 1. Galgame / Visual Novel Localization Pipeline
```bash
site:tieba.baidu.com "汉化" "工具" ("没人" OR "缺" OR "不稳定" OR "打包器")
site:tieba.baidu.com "SiglusExtract" OR "Ren'Py" OR "KiriKiri" OR "Tyrano" ("提取" OR "回写" OR "打包") ("失败" OR "不稳定" OR "没工具")
site:tieba.baidu.com "MTool" OR "Translator++" OR "AiNiee" ("不支持" OR "缺" OR "只翻译")
```
**Key Signals Found**:
- "SiglusExtract 打包器过于不稳定几乎不可用" (tieba)
- "每个引擎都要单独找工具" / "文本提取→MT→术语表→回写→打包→测试，全靠手搓脚本" (zhihu/tieba)
- "MTool 只支持 RPGMaker" / "Translator++ 闭源、学习曲线陡峭" / "AiNiee 仅做翻译，不做提取/回写/打包" (this session)

#### 2. Dialect / Regional Language ASR
```bash
site:tieba.baidu.com "方言" OR "粤语" OR "四川话" OR "闽南语" OR "东北话" OR "客家话" OR "吴语" ("语音转文字" OR "识别" OR "ASR") ("没法用" OR "准确率低" OR "没有" OR "只有普通话")
site:tieba.baidu.com "Qwen3-ASR" OR "Whisper" OR "FunASR" ("方言" OR "微调") ("效果差" OR "不会微调")
```
**Key Signals Found**:
- "讯飞/通义只支持普通话/粤语/英语" / "四川话/闽南语/东北话/客家话/吴语 转文字基本没法用" (zhihu/tieba)
- "Qwen3-ASR 支持 52 语种但方言准确率极低" / "无方言适配微调+离线部署一体化工具" (this session)

#### 3. Classical Chinese Text Processing
```bash
site:tieba.baidu.com "古籍" OR "竖排" OR "繁体" OR "方志" OR "家谱" ("断句" OR "标点" OR "识别" OR "校勘" OR "人名" OR "地名") ("工具" OR "开源") ("没有" OR "缺" OR "只能识别")
site:tieba.baidu.com "PaddleOCR" OR "Umi-OCR" ("古籍" OR "竖排") ("不断句" OR "不标点" OR "不识别书名号")
```
**Key Signals Found**:
- "PaddleOCR 能识别但不断句、不标点、不识别书名号/人名/地名" (zhihu)
- "断句/校勘/人名地名链接全靠人工" / "竖排版面阅读顺序、注文/夹注/双行注识别没工具" (this session)

#### 4. Game MOD Production Toolchain (Bethesda/Paradox/Unity)
```bash
site:tieba.baidu.com "Creation Kit" OR "CK" ("Steam版" OR "版本对应" OR "降版本") ("地狱" OR "困难" OR "没工具")
site:tieba.baidu.com "FO4Edit" OR "SSEEdit" OR "xEdit" ("无Python" OR "无API" OR "无批量" OR "无可视化")
site:tieba.baidu.com "DSD" OR "Dynamic String Distributor" ("手改JSON" OR "VSC编译" OR "报错全靠猜")
```
**Key Signals Found**:
- "Creation Kit 只能 Steam 版启动、版本对应地狱" / "FO4Edit/SSEEdit/xEdit 系列全是 Pascal/Delphi，无 Python/API" (tieba)
- "DSD 配置要手改 JSON、VSC 编译、报错全靠猜" / "无 MOD 制作可视化编排器" (this session)

#### 5. Offline Multimodal Assistant for Visually Impaired / Elderly
```bash
site:tieba.baidu.com "盲人" OR "视障" OR "老年人" ("吃药" OR "导航" OR "识别药盒" OR "障碍物") ("工具" OR "APP" OR "眼镜") ("没有" OR "联网" OR "不好用" OR "离线")
site:tieba.baidu.com "AI导盲" OR "导盲眼镜" ("开源" OR "离线" OR "国产芯片") ("没有" OR "只有Demo")
```
**Key Signals Found**:
- "药盒无盲文、字太小、扫码要网、AI眼镜要联网、离线完全不可用" (zhihu)
- "1700万视障 + 2.6亿老年人，药盒识别、室内导航、障碍物预警、公交到站——全靠人陪" (zhihu/this session)
- "AI导盲眼镜多为硬件众筹/实验室Demo，无成熟软件产品" (this session)

## Cross-Platform Gap Validation

### Zhihu Gap Patterns
```bash
site:zhihu.com ("没人做" OR "没人开发" OR "空白" OR "冷门") ("需求" OR "工具" OR "开源")
site:zhihu.com "求推荐" ("没有" OR "缺") ("开源" OR "工具")
site:zhihu.com "有没有" ("现成" OR "开箱即用") ("工具" OR "方案") ("没有" OR "都不好用")
```

### Bilibili Gap Patterns
```bash
site:bilibili.com ("开源" OR "GitHub") ("神器" OR "推荐") -("下载" OR "视频" OR "PDF")  # Exclude saturated areas
site:bilibili.com "冷门" "开源" "工具" "推荐"
site:bilibili.com "自制" "工具" "分享" "GitHub"  # Self-made tools = gap
```

## Gap Validation Workflow

### Step 1: Collect Gap Signals (3-5 days monitoring)
- Run gap search patterns daily
- Collect thread URLs, reply counts, bounty amounts
- Note authority opinions (mods, big-Vs, practitioners)

### Step 2: GitHub Absence Verification
```bash
# For each candidate gap, search GitHub
github.com search: <pain point keywords> language:Python stars:>10 pushed:>2024-01-01
github.com search: <pain point keywords> language:TypeScript stars:>10 pushed:>2024-01-01
# If 0-2 results with low stars/old pushes → TRUE GAP signal
```

### Step 3: Technical Feasibility Triage
| Gap | Existing Libs/Models | Blocker Type | MVP Effort |
|-----|---------------------|--------------|------------|
| Galgame pipeline | unrpyc, krkrz, GARbro, MTool | Engineering (integration) | Medium |
| Dialect ASR | Whisper, FunASR, Qwen-ASR | Data (dialect corpus) | Medium |
| Classical text | PaddleOCR, 古BERT | Engineering + Domain | High |
| MOD toolchain | xEdit (Pascal), CK (C++) | Reverse engineering | High |
| Visual assist | Qwen2.5-VL, YOLO, Piper TTS | Hardware + Optimization | Medium |

### Step 4: Score & Prioritize
Use the 50-point Gap Scoring Rubric in SKILL.md section 7.4

## Gap vs. Bad Solution Decision Tree
```
User complains about X
    │
    ├─► Search GitHub for X solutions
    │       │
    │       ├─► 0-2 repos, <50 stars, >1yr inactive → TRUE GAP
    │       │
    │       └─► 5+ repos, some active → Check community replies
    │               │
    │               ├─► "部署难/配置复杂/文档英文/有Bug" → BAD SOLUTIONS (wrap/polish opportunity)
    │               │
    │               └─► "功能缺失/不支持我的场景/核心流程断裂" → PARTIAL GAP (fork/extend opportunity)
    │
    └─► Search Tieba/Zhihu for "X 没人做/求开发/悬赏"
            │
            ├─► Multiple bounty posts + authority "暂无方案" → TRUE GAP
            │
            └─► Only "同问/收藏" no substance → WEAK SIGNAL, monitor
```

## Output Template: Gap Opportunity Card

```markdown
### Gap: <Short Name>
**Score**: XX/50 | **Confidence**: High/Med/Low

**Pain Point (User Voice)**
> "<verbatim quote from thread>"

**Demand Evidence**
- Threads: N (links) | Recurrence: X days | Bounties: ¥X
- Authority: <mod/big-V quote>
- Workarounds: <custom scripts / manual / freelancers>

**Solution Landscape**
- GitHub: <0 / N low-quality / N partial>
- Commercial: <none / enterprise-only $$$>

**Technical Path**
- Core libs: <lib1, lib2, model>
- Blockers: <data access / reverse eng / legal / compute>
- MVP: <3-5 features>

**Moat & GTM**
- Barrier: <data / domain / reverse eng / hardware>
- First 100 users: <specific communities>
- Monetization: <SaaS / license / service / donation>
```

## Anti-Patterns in Gap Discovery

❌ **Confusing "no good GUI" with "no solution"** — CLI tools exist, gap is packaging
❌ **Ignoring legal/ToS blockers** — video download, game reverse eng, paid API scraping
❌ **Overestimating "willingness to pay"** — "希望免费" ≠ paying customer
❌ **Single-source validation** — must cross-check Tieba + Zhihu + GitHub + Bilibili
❌ **Chasing "cool tech" without user** — verify real users with budget exist first
❌ **Underestimating maintenance burden** — niche tools need long-tail support
❌ **Trusting marketing revenue claims** — "月入 10 万" without platform backend proof = course seller
❌ **Confusing "high demand" with "high monetizable demand"** — free users ≠ paying customers
❌ **Ignoring platform policy volatility** — WeChat/闲鱼/抖音 change rules quarterly, can kill model overnight

## Real Monetization Reality Checks (This Session — Verified vs Marketing Claims)

### 1. WeChat Mini Program Flow Master (流量主)
| Metric | Marketing Claim | **Verified Reality (Zhihu实测贴)** |
|--------|----------------|-----------------------------------|
| **开通门槛** | "零门槛" | 累计 UV ≥ 1000，无违规记录 |
| **分成比例** | "高收益" | 微信抽 50%（创意小游戏 30%） |
| **eCPM 真实值** | "几十上百" | 激励视频 27.84 / 原生模板 2.82 / 插屏 2.70 |
| **点击率真实值** | "高点击" | 激励 8.17% / 原生 0.25% / 插屏 0.17% |
| **DAU 2000 实测** | "日入 500+" | **日均 55 元**，月约 **1650 元** |
| **结算周期** | "快速到账" | 半月结（次月 1 号 / 15 号） |
| **矩阵要求** | "单个就够" | **必须 10-20 个矩阵**，总 DAU 2-3 万 → 月入 3-8K |
| **核心壁垒** | "搭建即赚" | 关键词 SEO + 激励视频植入设计 + 矩阵互导流 |
| **政策风险** | "长期稳定" | **极高** — 2021 年曾永久关闭入口，随时收紧审核/分成 |

### 2. 闲鱼虚拟资料/模板店群
| Metric | Marketing Claim | **Verified Reality (知乎实测 + 血泪教训贴)** |
|--------|----------------|-----------------------------------|
| **单号月收入** | "月入过万轻松" | **3559 元 / 30 天**（实测贴《30天1个号赚了3559元》） |
| **新手首单** | "当天出单" | 首单约 48 小时，首月 1-3K 常见 |
| **矩阵上限** | "无限放大" | 1 人 3 号（支付宝实名限制），月入 5-10K 封顶 |
| **客单价** | "高客单" | 9.9-29.9 元主流，高客单 50-99 元极难出单 |
| **版权/侵权" | "无风险" | **极严** — 一旦投诉直接下架+限流+扣分，资料类重灾区 |
| **价格战" | "高利润" | "价格从 150 降到 9 毛 9"，**时薪不足 5 块** |
| **账号关联" | "多号没事" | **同 IP/设备/环境直接判关联限流**，矩阵成本极高 |
| **售后/差评" | "无售后" | **虚拟商品无法申诉**，差评直接权重归零 |
| **自动发货" | "全自动" | **首单必须人工**，第二单才能开自动发货 |
| **真实可行路径" | "铺货躺赚" | **只做非标准化/强服务/强定制**：AI 定制简历/PPT/提示词/代跑脚本 → 客单 50-200 |

### 3. Chrome/Edge 浏览器插件
| Metric | Marketing Claim | **Verified Reality (DebugBear/konabayev 2024-2026 统计)** |
|--------|----------------|-----------------------------------|
| **总扩展数" | "机会多" | ~178,299（2026 Q1），年增 22.7% |
| **中位数安装数" | "易推广" | **仅 18 个用户** |
| **70.4% 扩展" | "有市场" | **≤ 100 用户** |
| **85% 扩展" | "能跑通" | **< 1000 安装** |
| **成功扩展均值" | "月入几万" | $862K/年（$72.8K/月）——**仅前 0.1%** |
| **独立开发者实测" | "周末上架即赚" | 2K-10K 活跃用户 → $50-1,500/月；10K-50K → $500-7,500/月 |
| **前 3 个月" | "快速变现" | **0 收入是常态**（SEO 起效 3-6 个月） |
| **Manifest V3" | "无影响" | 2025 强制，老扩展大量失效/下架 |
| **真实可行路径" | "通用工具" | **避开生产力/Workflow 红海**，做垂直细分痛点：特定网站数据导出/特定平台批量操作/特定行业合规检查 |

### 4. AI 提示词/工作流模板 (Gumroad/闲鱼/知识星球)
| Metric | Marketing Claim | **Verified Reality (dollarflourish 追踪 + 知乎血泪贴)** |
|--------|----------------|-----------------------------------|
| **服务类第 6 月" | "月入几万" | **$500-1,500**（约 3.5-10K 人民币） |
| **Gumroad 成功卖家" | "高单价" | 模板 $47-147，月销 **20-200 单** |
| **闲鱼提示词单价" | "高利润" | **9.9-99 元**，定制服务 50-200 元/单 |
| **内容账号变现" | "快速变现" | 3-12 个月才能跑平台分成 |
| **核心坑点" | "一次制作多次售" | **极易被复制/盗版** — "一份资料卖 9 毛 9"，无护城河 |
| **平台收割" | "平台扶持" | Gumroad 抽 10%+手续费、闲鱼限流/下架、知识星球扣点高 |
| **售后无尽头" | "无售后" | "反复沟通、多次修改、折算时薪远低于预期" |
| **真实可行路径" | "卖模板" | **不卖通用提示词，卖已验证工作流/自动化脚本** + 部署文档 + 售后群 + 年度更新 → LTV 提升 5-10 倍 |

### 5. 桌面端小工具
| Metric | Marketing Claim | **Verified Reality** |
|--------|----------------|-----------------------------------|
| **分发渠道" | "易分发" | Microsoft Store（审核 3-7 天，抽成 15%）、GitHub Release、官网+Stripe/Paddle、闲鱼自动发货 |
| **变现模式" | "高客单" | 买断制 9.9-49 元、订阅制 9.9-29.9 元/月、免费+捐赠/广告 |
| **典型单人收入" | "月入几万" | **头部 5-50K**，长尾 < 500 元 |
| **杀毒软件误报" | "无影响" | **极高**（PyInstaller/Go/Rust 必中招），需 EV 代码签名证书 $300-600/年 |
| **国内付费意愿" | "强" | **极度白嫖**，破解版满天飞，**海外市场才是主战场** |
| **兼容性坑" | "简单" | Win10/11、高 DPI、多显示器、权限隔离、自启动、托盘图标 — 坑极多 |
| **真实可行路径" | "上架即赚" | **海外首发**：Product Hunt / Hacker News / Reddit / Indie Hackers → 拿美元 |

## Automation: Gap Monitoring Pipeline

### RSSHub Feeds for Gap Keywords
```
# Custom keyword feeds (if RSSHub supports)
https://rsshub.app/tieba/keyword/没人做/开源/工具
https://rsshub.app/tieba/keyword/求开发/悬赏/工具
https://rsshub.app/tieba/keyword/冷门/需求/开源
```

### TrendRadar / MediaCrawler Keywords for Gaps
```
没人做 开源 工具
求开发 悬赏 脚本
冷门 需求 开源
全网找不到 GitHub
急需 工具 没有
```

### Weekly Gap Review Checklist
- [ ] New gap signals collected this week
- [ ] GitHub absence re-verified for top 5 gaps
- [ ] Technical feasibility updated (new libs/models released?)
- [ ] Community discussion evolved? (new bounties, workarounds, authority opinions)
- [ ] Score updates → reprioritize

---

## Session Reference: Gaps Discovered 2026-10

| Gap | Score | Status | Notes |
|-----|-------|--------|-------|
| Galgame Localization Pipeline | 42/50 | Validated | High demand, clear tech path, strong moat (engine diversity) |
| Dialect ASR Fine-tune Toolkit | 38/50 | Validated | Clear path with Whisper/FunASR, data is main blocker |
| Classical Text Workstation | 35/50 | Validated | High domain expertise needed, academic partnerships possible |
| MOD Production Workbench | 32/50 | Validated | High reverse eng effort, but Bethesda/Paradox communities large |
| Offline Visual Assist SDK | 40/50 | Validated | Policy tailwinds, hardware partners (RK3588/orangepi), clear GTM |

*Update quarterly or when new gap signals emerge.*
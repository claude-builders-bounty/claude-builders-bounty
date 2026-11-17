---
name: chinese-community-demand-research
description: Find niche Chinese community problems with GitHub solutions AND discover true underserved demand (gaps where demand exists but no good solution exists).
trigger: User needs validated demand-solution pairs from Chinese communities for product ideation, OR user asks for "cold starts" / "nobody is building this" / "blue ocean" opportunities with real demand evidence.
---

# Chinese Community Demand Research

## When to Use
- Discovering "small audience, big pain" problems on Tieba/Zhihu/Bilibili/Xiaohongshu
- Validating whether a GitHub project actually solves a real user pain point
- Building a pipeline: community signal → GitHub project → maturity check → opportunity scoring

## Core Workflow

### 0. Legal & Compliance Risk Screening (MANDATORY FIRST STEP)
Before any demand research, filter out directions with legal/ToS risk:

| Risk Category | Examples | Action |
|---------------|----------|--------|
| **Government/Judicial/Regulatory Sites** | Court documents (裁判文书网), Bidding platforms (公共资源交易中心), Drug regulation (NMPA), Patent office (CNIPA), Customs (海关总署) | **HARD REJECT** — scraping/monitoring violates ToS, may constitute illegal access, exposes operator to criminal liability |
| **Paid API / Walled Garden Scraping** | WeChat private APIs, Douyin/TikTok private APIs, Xianyu private APIs (non-official), Paid SaaS scraping | **REJECT** — ToS violation, account/IP bans, potential CFAA/Computer Fraud equivalent in CN |
| **DRM / Copyright Circumvention** | Video downloader (encrypted streams), Game asset extraction (Denuvo/DRM), Paid content bypass | **REJECT** — DMCA/CN Copyright Law violation |
| **Reverse Engineering Commercial Software** | Game engine internals (Unity/Unreal encrypted assets), Proprietary format parsers | **CAUTION** — EULA violation, only if clean-room + interoperability exception |
| **Personal Data / PII** | User profile scraping, Chat log analysis without consent, Location tracking | **REJECT** — PIPL/CSL/GDPR violation |

**Rule**: If the data source requires bypassing authentication, encryption, rate limits, or ToS — STOP. Do not research demand for it. The user explicitly rejected government site monitoring: "你让我去爬政府网站？你打算把我送进监狱".

### 1. Target Community Selection
Focus on high-signal, technical/hobbyist bars:
| Community | High-Signal Bars | Search Keywords |
|-----------|------------------|-----------------|
| **Tieba** | `Linux吧` `Python吧` `开源软件吧` `程序员吧` `Kindle吧` `电子书吧` `Calibre吧` `Rime吧` `PT吧` `NAS吧` `软路由吧` `下载吧` `视频下载吧` `去水印吧` `贴吧签到吧` `吧务吧` | `"GitHub" "开源" "求推荐" OR "有没有工具" OR "痛点" OR "批量下载" OR "去水印" OR "自托管" OR "本地部署"` |
| **Zhihu** | Questions with "开源""GitHub""替代""自建""私有化" | Same patterns + "知乎" |
| **Bilibili** | Tool review videos, "GitHub 神器""开源项目推荐" | Video titles + comments |
| **Xiaohongshu** | "效率工具""开源""自建""NAS""私有云" | Hashtag search |

### 2. Search Patterns (Baidu `site:tieba.baidu.com`)
```bash
# Core pattern
site:tieba.baidu.com "GitHub" "开源" ("求推荐" OR "有没有工具" OR "痛点" OR "怎么解决")

# Specific pain points
site:tieba.baidu.com "批量下载" "GitHub" "开源" "求"
site:tieba.baidu.com "去水印" "GitHub" "开源" "推荐"
site:tieba.baidu.com "自托管" "开源" "替代" "推荐"
site:tieba.baidu.com "Kindle" "Calibre" "GitHub" "推送"
site:tieba.baidu.com "Rime" "雾凇" "词库" "GitHub"
```

### 3. Signal Validation Checklist
A thread is **high-signal** when:
- [ ] Same question appears in multiple threads over weeks/months
- [ ] Replies recommend half-baked scripts, paid tools, or "figure it yourself"
- [ ] Bar moderators/big-Vs acknowledge the gap ("暂时没有完美方案")
- [ ] Commercial solutions exist but are expensive/limited/ads-ridden
- [ ] Comments show "GitHub 有项目但不会部署/报错/文档全英文"
- [ ] **Practitioner income reports** — verified users sharing actual revenue numbers (not course sellers)

### 3.1 Individual-Executable Validation (User Requirement: "落地难，找适合个人的")
A direction is **individually executable** ONLY when ALL pass:
- [ ] **Zero team dependency** — single person can build, deploy, operate, support
- [ ] **Zero enterprise sales cycle** — no B2B contracts, procurement, legal review
- [ ] **Platform-native distribution** — WeChat Mini Program / Chrome Web Store / Gumroad / 闲鱼 / Microsoft Store (no custom infra)
- [ ] **T+1 to T+7 cash flow** — platform direct payout, no net-30/60/90
- [ ] **Maintenance < 10 hrs/week** — automated ops, self-serve users, minimal support
- [ ] **Startup cost < ¥5,000** — no inventory, no paid ads required, dev tools only

**Reject** if any fail: enterprise SaaS, marketplace platforms, hardware, regulated industries, team-required ops.

### 3.3 Agent-Automation Validation (User Requirement: Agent 全托管)
A direction is **Agent-automatable** ONLY when ALL pass:
- [ ] **Parameterizable workflow** — core process can be expressed as parameters + templates (not bespoke craft per job)
- [ ] **Deterministic verification** — Agent can verify output quality via automated checks (tests, lint, schema, diff)
- [ ] **Low human-in-loop** — < 20% steps require human judgment; rest are code-gen/execute/verify
- [ ] **Reusable code assets** — same stack/templates reusable across customers (not one-off custom)
- [ ] **Observability built-in** — logs/metrics/telemetry feed back to Agent for self-correction

**Reject** if any fail: high-touch consulting, per-client customization, creative/artistic judgment, physical ops, regulatory interpretation.

**Examples from this session — REJECTED (Agent不可自动化)**:
- Galgame localization pipeline: engine diversity requires per-title reverse engineering, termbase curation needs human
- Dialect ASR toolkit: data collection/annotation/validation requires native speakers, not automatable
- Ancient text workstation: scholarly judgment (punctuation, named entities) requires domain experts
- MOD production workbench: reverse engineering per game engine, creative asset integration
- Visual assist SDK: hardware integration, accessibility testing with real users, regulatory (medical device)

### 3.2 Anti-Marketing-Hype Verification (User Requirement: "别看营销话术，去筛选一下是否真正可落地")
Distinguish **real practitioner data** from **marketing/course-seller hype**:

| Source Type | Identification Pattern | Trust Level |
|-------------|------------------------|-------------|
| **Real Practitioner** | "我做了 X 天，首单第 Y 天，月入 Z 元" + platform backend screenshots (blurred) + specific metrics (DAU, conversion, CAC) + admits failures/difficulties | **HIGH** |
| **Real Practitioner** | "血泪教训" / "踩坑" / "避坑指南" — shares losses, account bans, revenue drops, specific platform policy changes | **HIGH** |
| **Course Seller / Marketing** | "零基础日入过千" / "月入十万" / "躺赚" / "全自动" / "无脑操作" / "保姆级教程" / "扫码进群领资料" | **ZERO** — these sell courses, not operate businesses |
| **Course Seller / Marketing** | Only shows peak revenue screenshot, no timeline, no failure mentions, pushes paid community/course in bio | **ZERO** |
| **Platform Official** | WeChat Mini Program flow stats, Chrome Web Store install counts, Gumroad public revenue pages | **MEDIUM** — aggregate, not individual |

**Verification Protocol**:
1. Search author history — if they sell courses/consulting → discount 90%
2. Demand specific metrics — "上周 DAU 多少？转化率？客单价？获客成本？"
3. Cross-platform check — same person on 闲鱼/知乎/小红书/X with consistent story?
4. Timeline check — "3个月月入 5 万" → ask for month 1, 2, 3 breakdown
5. Platform policy awareness — real operators cite recent policy changes (e.g., 闲鱼虚拟品 2024.04 放宽管控, 2025 严打侵权)

### 4. GitHub Project Maturity Assessment (Priority Order)
1. **README + Docs**: Chinese README, install guide, Docker/Release/Action one-click deploy
2. **Activity**: Recent commits, open/closed issue ratio, author responsiveness
3. **Stars/Forks Trend**: `github-weekly-rank` / `github-trending` appearance
4. **Third-party Validation**: Tutorials on 少数派/知乎/CSDN/B站, not just README
5. **License**: MIT/Apache-2.0/GPL-3.0 (commercial-friendly if needed)

### 5. Pain Point → Project Mapping Template
| Pain Point | Typical User Query | Representative GitHub Projects | Maturity (★-★★★★★) | Gap |
|------------|-------------------|-------------------------------|---------------------|-----|
| Full-platform video batch download | "抖音/快手/小红书/B站/视频号怎么批量下载无水印？" | `cshuangyy/videdown` `NanmiCoder/MediaCrawler` `jiji262/douyin-downloader` `yt-dlp/yt-dlp` | ★★★★☆ | Windows GUI, scheduled tasks |
| B站 high-quality batch download | "B站 8K/HDR/杜比/批量/弹幕/字幕怎么下？" | `ScottSloan/Bili23-Downloader` `erikzhuang55/Bilitato` | ★★★★☆ | Auto-update, plugin system |
| Tieba auto sign-in/moderation | "贴吧签到忘了/多账号/吧务审核累/想归档整个吧" | `chiupam/tieba` `shitianshiwa/Tieba-Cloud-Review` `nixliuxin/Tieba-Time-Machine` | ★★★☆☆ | Web dashboard, multi-account UI |
| E-book management/push | "Calibre 怎么用/推送进 Kindle/批量转 epub/去除 DRM" | `kovidgoyal/calibre` `talebook/talebook` `jbiaojerry/ebook-treasure-chest` | ★★★★★ | Mobile UI, OPDS sync |
| Novel/TXT reader with sources | "PC 端看小说/换源/朗读/护眼/开源" | `binbyu/Reader` | ★★★☆☆ | Epub rendering, cloud sync |
| Network disk high-speed download | "百度网盘限速/磁力链/种子怎么满速下？" | `Motrix/Motrix` `qBittorrent/qBittorrent` `XIU2/TrackersListCollection` | ★★★★★ | BaiduPan API stability |
| Rime config/maintenance | "小狼毫/雾凇/词库/自定义短语/同步" | `iDvel/rime-ice` `rime/rime` | ★★★★★ | GUI config tool |
| Local AI stack | "Ollama/Whisper/SD/离线翻译/本地跑模型" | `ollama/ollama` `openai/whisper` `AUTOMATIC1111/stable-diffusion-webui` `LunaTranslator/LunaTranslator` | ★★★★☆ | Unified installer, model mgmt |

### 6. Monitoring & Automation Setup
- **RSSHub** routes: `tieba/forum/<kw>`, `zhihu/search/<kw>`, `bilibili/search/<kw>`
- **TrendRadar** / `MediaCrawler` for keyword alerts (daily push to Feishu/Telegram)
- **GitHub Watch**: `star-history.com` + `github-weekly-rank` for project trajectory

## 7. Finding Underserved Demand (True Gaps — Demand Exists, No Good Solution)

### 7.0 Search Scope Expansion Protocol (User Requirement: "范围再扩大一点，别找重复的")
**When user says "expand range" or "stop repeating"**:
1. **Audit current coverage** — list all domains already searched (consumer apps, Internet tools, content platforms)
2. **Jump to adjacent verticals** — industrial, scientific, medical, engineering, hardware, regulated-but-compliant
3. **Search for "domain expert" bars** — not "programmer" bars; e.g., `机械设计吧` `化工仿真吧` `注塑吧` `光伏运维吧` `非标自动化吧` `BIM吧` `Revit吧` `PCB设计吧` `PLC编程吧` `上位机开发吧` `LabVIEW吧` `AspenPlus吧` `医疗器械注册吧` `专利代理吧`
4. **Use domain-specific gap patterns** — see references/industrial-vertical-patterns.md
5. **Validate with practitioners** — find 1-2 real engineers in the domain, verify pain + budget

**This session's expansion**: from consumer/Internet (12 saturated areas) → 5 niche tech → 5 gov/regulatory (rejected) → 5 enterprise (rejected) → 5 individual (reality-checked) → **10 industrial/vertical domains** (CAD/CAE/EDA/BIM plugins, PLC/HMI automation, injection molding optimization, solar/storage/charging O&M, chemical simulation workflows, medical data compliance, patent automation, non-standard automation kits, BIM/Revit automation, industrial vision deployment).

### 7.1 Industrial Vertical Domain Search Patterns (Baidu `site:tieba.baidu.com`)
```bash
# Mechanical/CAE/BIM/CAD
site:tieba.baidu.com ("SolidWorks" OR "AutoCAD" OR "中望" OR "Creo" OR "NX" OR "Inventor") ("插件" OR "二次开发" OR "API" OR "宏" OR "自动化") ("求" OR "没有" OR "缺")
site:tieba.baidu.com ("Revit" OR "Dynamo" OR "Navisworks" OR "BIM") ("插件" OR "二次开发" OR "自动化" OR "出图" OR "排布" OR "钢筋") ("求" OR "缺" OR "难用")
site:tieba.baidu.com ("ANSYS" OR "Abaqus" OR "Comsol" OR "HyperMesh" OR "CAE") ("前处理" OR "网格" OR "参数化" OR "脚本" OR "自动化") ("求" OR "没有" OR "繁琐")

# EDA/PCB/Hardware
site:tieba.baidu.com ("Altium" OR "KiCad" OR "Allegro" OR "PADS" OR "Cadence" OR "EDA") ("插件" OR "脚本" OR "插件" OR "自动化" OR "BOM" OR "规则检查") ("求" OR "缺" OR "没有")
site:tieba.baidu.com ("PCB" OR "原理图" OR "Layout" OR "SI" OR "PI" OR "EMC") ("外包" OR "接单" OR "兼职" OR "赚钱" OR "月入") ("真实" OR "实测" OR "避坑")

# Industrial Automation/PLC/HMI
site:tieba.baidu.com ("PLC" OR "西门子" OR "三菱" OR "欧姆龙" OR "施耐德" OR "Modbus" OR "Profinet") ("程序" OR "组态" OR "上位机" OR "WinCC" OR "触摸屏" OR "自动化") ("外包" OR "接单" OR "脚本" OR "标准化")
site:tieba.baidu.com ("非标" OR "自动化设备" OR "夹具" OR "治具" OR "视觉" OR "选型") ("电气" OR "EPLAN" OR "图纸" OR "BOM" OR "方案") ("外包" OR "接单" OR "缺人")

# Chemical/Process/Injection Molding
site:tieba.baidu.com ("注塑" OR "注塑工艺" OR "注塑参数" OR "调机" OR "试模") ("优化" OR "记录" OR "参数" OR "AI" OR "工艺单") ("求" OR "没有" OR "靠经验")
site:tieba.baidu.com ("Aspen" OR "HYSYS" OR "化工仿真" OR "工艺模拟" OR "精馏" OR "反应器") ("自动化" OR "脚本" OR "参数优化" OR "批量") ("求" OR "缺" OR "没有")

# Energy/Solar/Storage
site:tieba.baidu.com ("光伏" OR "储能" OR "充电桩" OR "逆变器" OR "BMS" OR "EMS") ("运维" OR "巡检" OR "监控" OR "自动化" OR "脚本" OR "报表") ("求" OR "缺" OR "人工")

# Medical/Regulatory (Compliant Only)
site:tieba.baidu.com ("医疗器械" OR "注册" OR "NMPA" OR "FDA" OR "ISO13485" OR "MDR") ("技术文档" OR "BOM" OR "风险管理" OR "临床评价") ("模板" OR "工具" OR "自动化" OR "缺")
site:tieba.baidu.com ("DICOM" OR "HL7" OR "FHIR" OR "PACS" OR "电子病历") ("转换" OR "清洗" OR "标准化" OR "对接" OR "工具") ("求" OR "没有" OR "缺")

# Patent/IP
site:tieba.baidu.com ("专利" OR "撰写" OR "代理" OR "检索" OR "分析" OR "布局") ("AI" OR "工具" OR "自动化" OR "草稿" OR "权利要求") ("求" OR "缺" OR "人工")

### 7.6 Verified Agent Monetization Platforms (This Session — Real Data, Not Marketing)

The following platforms have **verified transaction data** where individual operators run AI agents to earn money. Cross-referenced with platform public stats, user transaction logs, and independent audits.

| Platform | Model | Verified Volume | Typical Agent Earnings | Key Constraints |
|----------|-------|-----------------|------------------------|-----------------|
| **dealwork.ai** | Hybrid marketplace (Agent↔Human, Agent↔Agent) | 147 completed contracts since 2026-03-08 | $15-500/contract; top agents $2K+/mo | Research/Code/Writer tasks; AUTO_APPROVE 24h; 10% fee (3% Agent↔Agent); reputation system gates high-value jobs |
| **ClawMart** | Skill/Persona/Starter Pack marketplace | $100K+ paid to creators; 2000+ listings | $5-89/listing; top creators $1K-5K/mo | OpenClaw skills (SKILL.md + scripts); 15% platform fee; Stripe payout; Felix agent $125K/30d (outlier) |
| **Upwork / Fiverr** | Traditional freelance, AI-assisted delivery | 63B (2025) → 71.7B (2026 est) | $500-3K → $8K-12K/mo (AI-assisted devs managing 6-8 projects) | English required; Upwork 20% fee newbies; Fiverr micro-service model; reputation takes 3-6 months |
| **闲鱼虚拟资料/定制** | C2C marketplace, auto-delivery | 3-4 accounts/person; 3559 CNY/30d (real test) | 1-3K first month; 5-10K ceiling (3-account limit) | Real-name 3 accounts max; IP/device correlation; copyright takedowns; price wars (9.9 CNY floor); auto-delivery only after 1st manual |
| **OpenClaw + 自媒体平台** | Agent automates content pipeline → platform revenue | 6 days 1000+ CNY (short drama); 100 CNY/day (small account) | Variable; depends on platform CPM | Douyin/Kuaishou/Xiaohongshu revenue share; account ban risk; material copyright; token cost ($3K/mo heavy users) |
| **Gumroad / Lemon Squeezy** | Digital product marketplace (plugins, templates, courses) | $2.19M/week total creator revenue | $100-10K+/mo (top plugin creators) | Stripe/Paddle payout; 8.5%+30¢ fee; global reach; no platform discovery (self-marketing) |
| **Figma/Canva/Adobe Express/即时设计 Plugin Stores** | Platform-native plugin marketplace | UCharts: $226/mo after paid conversion; 即时设计激励 ¥13,800/2mo | $50-2K+/mo per plugin; matrix multiplies | Platform review; revenue share varies; locked to platform ecosystem |
| **Shopify App Store** | B2B SaaS app marketplace | WideBundle: $50K/mo (25yo, 3 failed apps prior) | $1K-50K+/mo; 16/mo per install avg | App review; B2B sales cycle; recurring revenue; high churn (25%) |

**Platform Selection Rules** (User Requirement: "不交学费、不囤货、不养号、不赌爆款、只做离钱最近的事"):
- **dealwork.ai** — lowest barrier, USD payout, Agent-native, start with $1-5 Research tasks to build reputation
- **ClawMart** — if you write Hermes/OpenClaw skills, package as SKILL.md, zero marginal cost per sale
- **Upwork/Fiverr** — if you have coding skills, package as fixed-scope services ("3h fix React bug")
- **闲鱼** — only for non-standardized/high-service/custom (AI resume/PPT/prompt/script), NOT commodity templates
- **Gumroad/Lemon Squeezy** — for plugins, templates, digital products; self-marketing required; USD payout
- **Figma/Canva/即时设计 Plugin Stores** — if you build design tools; platform distribution but locked ecosystem
- **Shopify App Store** — if you build B2B SaaS; recurring revenue but long sales cycle + review
- **OpenClaw自媒体** — token cost must be in P&L; platform policy volatility extreme; not primary path

**Verification Protocol for Any New Platform**:
1. Check platform public stats (total contracts, payouts, active agents)
2. Find 2-3 real operator transaction logs (not course sellers)
3. Verify payout method, timeline, fees, dispute rate
4. Calculate unit economics: revenue - (token + platform fee + ops time) = net
5. Stress-test: what if platform changes rules tomorrow? (闲鱼/WeChat/Douyin/Chrome Store change quarterly)

### 7.7 Newly Verified Individual-Executable Vertical Opportunities (This Session)

| Opportunity | Typical Monthly Revenue | Startup Cost | Core Stack | Agent Automation % | Verified Evidence |
|-------------|------------------------|--------------|------------|-------------------|-------------------|
| **KiCad/Altium Plugin → Gumroad** | $100-2K+ | $0 (Python + KiCad API) | Python, KiCad Action Plugin API, Gumroad | 90% (code gen + test + package) | SaludPCB: 3 plugins @ $5 each, sustained sales on Gumroad |
| **PCB Design/Reverse Engineering → Upwork** | $2K-8K | $0 (portfolio on GitHub) | Altium/KiCad, GitHub portfolio | 70% (schematic→layout→BOM→Gerber automation) | Upwork 257 active PCB jobs; Top Rated $60-92/hr |
| **Injection Molding Parameter Optimization Agent** | ¥5K-50K/project | ¥0 (if factory provides data) | Python, DOE/ML, factory data access | 80% (data→model→recommendation) | 知乎实测: "AI 一句不用问直接优化好了注塑参数" |
| **Shopify/Figma/Canva/即时设计 Plugin Matrix** | $50-10K+ | $0 (TS/React, platform SDKs) | TypeScript, React, platform SDKs, Gumroad/Stripe | 85% (core logic reuse across 4 platforms) | 小树出海: 38 plugins in 2mo, ¥13.8K奖金, UCharts $226/mo |
| **Embedded Firmware + PCB One-Stop Delivery** | $3K-15K | $0 (JLCPCB/LCSC for proto) | KiCad/Altium, STM32/ESP32, C/Rust, JLCPCB | 75% (schematic+PCB+firmware+BOM automation) | Upwork real projects: IoT dairy farm, breast pump, hydroponics, vending machine |
| **CAE/Simulation Pre-Processing Automation** | ¥3K-20K/project | ¥0 (ANSYS/Abaqus license via client) | Python/JS, ANSYS/Abaqus/中望 API | 80% (mesh/BC/parametric automation) | CAE engineers 20-40% salary premium; enterprises desperate for automation |
| **Electrical/Automation EPLAN/Non-Standard Design** | $2K-6K | $0 (EPLAN license via client) | EPLAN, Siemens/Mitsubishi PLC, electrical standards | 70% (schematic→PLC→BOM→cable list) | 电鸭/程序员客栈 long-term EPLAN/PLC outsourcing demand |
| **3D Printing Farm/Stencil/Fixture Design Delivery** | ¥3K-10K | ¥3K-10K (printers) | Slicer, CAD, printer farm management | 60% (slice/nest/print automation) | 知乎实测: "靠奴役 3D 打印机月入过万"; 注塑开模贵 → 小批量 3D 打印需求大 |

### When to Use
- User asks for "cold starts" / "nobody is building this" / "blue ocean" opportunities
- Validating whether a pain point genuinely lacks a solution vs. has bad solutions
- Building a pipeline: community gap signal → technical feasibility → opportunity scoring

### 7.1 Gap Discovery Search Patterns (Baidu `site:tieba.baidu.com`)
```bash
# Core gap patterns — users explicitly stating NO solution exists
site:tieba.baidu.com ("没人做" OR "没人开发" OR "没人搞" OR "空白" OR "缺失") ("工具" OR "软件" OR "开源")
site:tieba.baidu.com ("求开发" OR "求大佬做" OR "悬赏开发" OR "有偿开发") ("工具" OR "脚本" OR "程序")
site:tieba.baidu.com ("急需" OR "迫切需要" OR "强烈需求") ("没有" OR "缺") ("工具" OR "方案")
site:tieba.baidu.com ("冷门" OR "小众" OR "非主流") ("需求" OR "痛点") ("开源" OR "工具")

# Domain-specific gap patterns
site:tieba.baidu.com "汉化" "工具" ("没人" OR "缺" OR "不稳定")  # Galgame localization
site:tieba.baidu.com "方言" OR "粤语" OR "四川话" OR "闽南语" ("语音转文字" OR "识别") ("没法用" OR "准确率低" OR "没有")
site:tieba.baidu.com "古籍" OR "竖排" OR "繁体" ("断句" OR "标点" OR "识别") ("工具" OR "开源") ("没有" OR "缺")
site:tieba.baidu.com "MOD" "制作" "工具" ("Creation Kit" OR "xEdit" OR "FO4Edit") ("没人做" OR "不友好" OR "无API")
site:tieba.baidu.com "盲人" OR "视障" OR "老年人" ("吃药" OR "导航" OR "识别") ("工具" OR "APP") ("没有" OR "联网" OR "不好用")
```

### 7.2 Gap Validation Checklist
A thread indicates a **TRUE GAP** (not just bad solutions) when:
- [ ] **Explicit absence language**: "没有任何工具" / "全网找不到" / "GitHub 上没有" / "开源界空白"
- [ ] **Bounty/Commission posts**: "悬赏 X 元开发" / "有偿求大佬做" / "出钱找人写"
- [ ] **Domain experts confirm**: Bar mods / big-Vs / practitioners say "目前没有成熟方案" / "只能自己写脚本"
- [ ] **Workarounds are painful**: Replies show users writing custom scripts, manual processes, or paying freelancers
- [ ] **No GitHub results**: Searching the pain point + "GitHub" returns 0-2 repos, all abandoned/alpha
- [ ] **Technical feasibility confirmed**: At least one reply outlines a viable technical approach ("其实可以用 X + Y 做")
- [ ] **Willingness to pay**: Users discuss budget ("预算 500-2000") or time investment ("愿意花两周学")

### 7.3 Distinguishing True Gaps from "Bad Solutions Exist"
| Signal | **True Gap** | **Bad Solutions Exist** |
|--------|--------------|------------------------|
| GitHub search results | 0-2 repos, all <50 stars, >1yr inactive | 5+ repos, some 100+ stars, recent activity |
| Community replies | "没人做" / "悬赏开发" / "自己写脚本" | "用 XX 项目但部署难" / "XX 有 Bug" / "文档全英文" |
| Authority opinion | "暂无成熟方案" / "学术界也在研究" | "XX 项目功能全但配置复杂" |
| Commercial solutions | None, or enterprise-only $$$ | Exist but expensive/limited/ads |
| Technical blockers | Fundamental (no training data, no API, hard reverse engineering) | Engineering (packaging, config, docs, UI) |

### 7.4 Gap Scoring Rubric (0-10 each, Total 50)
| Criterion | Weight | Scoring Guide |
|-----------|--------|---------------|
| **Demand Evidence** | 10 | 10=bounty posts + recurrence; 5=recurring complaints; 2=single thread |
| **Solution Absence** | 10 | 10=0 GitHub results; 5=only alpha/abandoned; 2=bad but working solutions |
| **Technical Feasibility** | 10 | 10=clear path with existing libs; 5=research needed; 2=fundamental blockers |
| **Willingness to Pay** | 10 | 10=explicit budgets; 5=time investment discussed; 2=only "希望免费" |
| **Competitive Moat** | 10 | 10=high barrier (data, reverse eng, domain expertise); 5=moderate; 2=low |

### 7.5 Output: Underserved Opportunity Brief
```markdown
## Underserved Opportunity: <Name>
**Gap Score**: XX/50 | **Tier**: S/A/B/C

### Pain Point
<One-sentence user pain from community>

### Demand Evidence
- Threads: <links/count> | Recurrence: <days> | Bounties: <amounts>
- Willingness: <explicit budgets or time investment>

### Solution Absence
- GitHub: <0/low-star/abandoned repos>
- Commercial: <none / enterprise-only>
- Workarounds: <custom scripts / manual / freelancers>

### Technical Feasibility
- Approach: <libs/models/ APIs to combine>
- Blockers: <data access / reverse eng / compute / legal>
- MVP Scope: <3-5 core features>

### Moat & Business
- Barrier: <data / domain expertise / reverse eng / hardware>
- Target User: <specific persona>
- Monetization: <SaaS / license / service / donation>
- First 10 Users: <where to find them>
```

## Pitfalls & Anti-Patterns
- ❌ Trusting star count alone — many starred projects are unmaintained or CLI-only
- ❌ Ignoring deployment friction — if it needs `pip install` + config edit + cron, 90% users drop off
- ❌ Confusing "cool tech" with "pain people pay to solve" — validate willingness to pay (time/money)
- ❌ Single-source validation — cross-check Tieba + Zhihu + Bilibili + GitHub Issues
- ❌ Overlooking legal risk — video downloaders, scrapers, DRM removal operate in gray zones
- ❌ **Confusing "no good GUI" with "no solution"** — CLI tools exist, gap is packaging
- ❌ **Ignoring legal/ToS blockers** — video download, game reverse eng, paid API scraping
- ❌ **Overestimating "willingness to pay"** — "希望免费" ≠ paying customer
- ❌ **Chasing "cool tech" without user** — verify real users with budget exist first
- ❌ **Underestimating maintenance burden** — niche tools need long-tail support
- ❌ **Repeating same consumer/Internet domains** — expand to industrial/vertical when user says "重复"
- ❌ **Skipping Agent-automation validation** — if Agent can't automate 80%+, it's a service not a product
- ❌ **Trusting marketing revenue claims without platform backend proof** — "月入 10 万" + course seller bio = reject
- ❌ **Ignoring platform policy volatility** — WeChat/闲鱼/抖音/Chrome Store change rules quarterly, can kill model overnight
- ❌ **Overlooking overseas-first requirement** — domestic users won't pay for tools; sea-first for USD revenue
- ❌ **Missing EV code signing requirement** — PyInstaller/Go/Rust desktop tools WILL trigger AV without EV cert ($300-600/yr)
- ❌ **Assuming "industrial = hard" without checking plugin/script layer** — CAD/CAE/EDA/PLC plugin APIs are well-documented; the hard part is domain Know-how, not the API
- ❌ **Skipping "parameterizable workflow" check for Agent automation** — if every project needs custom reverse engineering, Agent can't scale; reject or find the parameterizable slice
- ❌ **Forgetting token cost in P&L for heavy Agent workflows** — OpenClaw heavy users burn $3K/mo token; unit economics must include token cost per deliverable
- ❌ **Ignoring that platforms require EV cert for desktop distribution** — Microsoft Store requires $19 dev account + EV cert; without EV, SmartScreen kills conversion
- ❌ **Treating "first dollar" as success metric without repeatability** — first sale may be luck; validate 3+ sales with same funnel before scaling

## Output Deliverables
1. **Demand Map**: Markdown table (pain point × frequency × urgency × existing solutions)
2. **Project Scorecard**: Each candidate project with maturity score + deployment friction score
3. **Opportunity Brief**: Top 3 opportunities with "build vs wrap vs promote" recommendation
4. **Underserved Opportunity Brief**: For true gaps (section 7.5) — gap score, technical path, moat, GTM
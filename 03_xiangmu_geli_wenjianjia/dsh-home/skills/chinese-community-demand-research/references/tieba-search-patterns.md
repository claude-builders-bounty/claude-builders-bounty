# Tieba Search Patterns — Battle-Tested Baidu Queries

## Core Discovery Patterns

### Generic "GitHub + Open Source + Pain" Pattern
```bash
site:tieba.baidu.com "GitHub" "开源" ("求推荐" OR "有没有工具" OR "痛点" OR "怎么解决")
```

### Specific High-Signal Pain Points

#### Video/Image Download & Watermark Removal
```bash
site:tieba.baidu.com "批量下载" "GitHub" "开源" "求"
site:tieba.baidu.com "去水印" "GitHub" "开源" "推荐"
site:tieba.baidu.com "视频号" "下载" "GitHub" "开源"
site:tieba.baidu.com "抖音" "批量" "GitHub" "开源"
site:tieba.baidu.com "小红书" "图集" "下载" "GitHub"
site:tieba.baidu.com "B站" "8K" OR "HDR" OR "杜比" "下载" "GitHub"
```

#### Tieba Ecosystem Tools
```bash
site:tieba.baidu.com "贴吧" "签到" "GitHub" "开源" "多账号"
site:tieba.baidu.com "吧务" "审核" "云审核" "GitHub" "脚本"
site:tieba.baidu.com "贴吧" "归档" "时光机" "GitHub" "开源"
site:tieba.baidu.com "贴吧" "客户端" "第三方" "GitHub" "开源"
```

#### E-book / Kindle / Calibre
```bash
site:tieba.baidu.com "Kindle" "Calibre" "GitHub" "推送"
site:tieba.baidu.com "电子书" "管理" "GitHub" "开源" "推荐"
site:tieba.baidu.com "Calibre" "Web" "服务" "GitHub" "开源"
site:tieba.baidu.com "小说" "阅读器" "书源" "GitHub" "开源"
site:tieba.baidu.com "epub" "转换" "GitHub" "开源" "批量"
```

#### Rime / Input Method
```bash
site:tieba.baidu.com "Rime" "雾凇" "词库" "GitHub"
site:tieba.baidu.com "小狼毫" "配置" "GitHub" "开源" "同步"
site:tieba.baidu.com "中州韵" "方案" "GitHub" "维护"
```

#### Self-Hosted / NAS / Private Cloud
```bash
site:tieba.baidu.com "自托管" "开源" "替代" "推荐"
site:tieba.baidu.com "NAS" "Docker" "GitHub" "开源" "部署"
site:tieba.baidu.com "私有云" "开源" "GitHub" "搭建"
site:tieba.baidu.com "RSSHub" "部署" "GitHub" "开源"
```

#### Network Disk / Download Acceleration
```bash
site:tieba.baidu.com "百度网盘" "限速" "GitHub" "开源" "下载"
site:tieba.baidu.com "磁力链" "下载" "GitHub" "开源" "客户端"
site:tieba.baidu.com "Motrix" OR "qBittorrent" "GitHub" "配置"
```

#### Local AI Stack
```bash
site:tieba.baidu.com "Ollama" "本地" "部署" "GitHub" "模型"
site:tieba.baidu.com "Whisper" "语音转文字" "GitHub" "开源" "离线"
site:tieba.baidu.com "Stable Diffusion" "本地" "GitHub" "整合包"
site:tieba.baidu.com "离线翻译" "GitHub" "开源" "LunaTranslator"
```

## High-Signal Bar List (Priority Order)

### Tier 1 — Core Technical/Hobbyist
- `Linux吧` `Python吧` `开源软件吧` `程序员吧`
- `Kindle吧` `电子书吧` `Calibre吧`
- `Rime吧` `小狼毫吧` `雾凇拼音吧`
- `PT吧` `NAS吧` `软路由吧` `Docker吧`

### Tier 2 — Tool-Specific
- `下载吧` `视频下载吧` `去水印吧` `批量下载吧`
- `贴吧签到吧` `吧务吧` `云审核吧`
- `小说阅读器吧` `TXT阅读器吧` `书源吧`

### Tier 3 — Adjacent High-Signal
- `开源硬件吧` `树莓派吧` `软路由吧` `黑群晖吧`
- `效率工具吧` `生产力工具吧` `自动化吧`

### Tier 4 — Practitioner Income / Blood Posts (High Trust)
- `副业吧` `兼职吧` `网赚吧` `闲鱼吧` `小红书运营吧`
- `独立开发吧` `个人开发者吧` `MicroSaaS吧` `IndieHackers吧`
- `Chrome扩展吧` `浏览器插件吧` `小程序开发吧`

#### Practitioner Income / Blood Posts (High Trust)
```bash
# Real income reports with metrics
site:tieba.baidu.com ("实测" OR "实操" OR "复盘" OR "血泪" OR "踩坑" OR "避坑") ("月入" OR "日入" OR "流水" OR "利润") ("闲鱼" OR "小红书" OR "小程序" OR "插件" OR "独立开发")

# Blood/lessons posts
site:tieba.baidu.com ("血泪教训" OR "踩坑" OR "避坑指南" OR "被封" OR "限流" OR "侵权") ("闲鱼" OR "小红书" OR "小程序" OR "虚拟" OR "流量主")

# Specific platform reality checks
site:tieba.baidu.com "闲鱼" "虚拟" ("血泪" OR "踩坑" OR "被封" OR "限流" OR "9毛9" OR "价格战")
site:tieba.baidu.com "小程序" "流量主" ("实测" OR "真实" OR "日均" OR "eCPM" OR "点击率")
site:tieba.baidu.com "Chrome插件" OR "浏览器插件" ("月入" OR "变现" OR "独立开发" OR "上架")

# Independent developer real revenue
site:zhihu.com ("独立开发" OR "个人开发" OR "MicroSaaS") ("月入" OR "MRR" OR "流水" OR "变现") ("真实" OR "实测" OR "复盘" OR "血泪")
site:zhihu.com "独立开发者" ("月入" OR "年入") ("真实" OR "避坑" OR "踩坑" OR "教训")
```

## Search Operators Cheatsheet

| Operator | Example | Purpose |
|----------|---------|---------|
| `site:` | `site:tieba.baidu.com` | Restrict to Tieba |
| `""` | `"GitHub"` | Exact phrase match |
| `OR` | `"求推荐" OR "有没有工具"` | Boolean OR |
| `()` | `("A" OR "B") "C"` | Grouping |
| `-` | `GitHub -广告 -推广` | Exclude noise |
| `intitle:` | `intitle:求推荐` | Title only |
| `inurl:` | `inurl:p/ "GitHub"` | URL pattern |

## Validation Heuristics

### High-Signal Thread Indicators
1. **Recurrence**: Same question in 3+ threads over 30+ days
2. **Reply Quality**: Top replies are workarounds, paid tools, or "google it"
3. **Authority Gap**: Bar mods/big-Vs say "暂时没有完美方案"
4. **Commercial Pain**: Existing paid tools are expensive/limited/ads
5. **Deployment Barrier**: "GitHub 有项目但不会部署/报错/全英文文档"
6. **Practitioner Income Proof**: Verified backend screenshots (blurred) + specific metrics + admits failures
7. **Blood/Lessons Posts**: "血泪教训" / "踩坑" / "避坑" — shares losses, bans, revenue drops, policy changes

### Low-Signal / Noise Indicators
- Single thread, no replies, or only "mark/收藏"
- OP asks for cracked/paid software
- Thread is pure chat/venting without specific tool request
- Replies are all "同问" without substance

### **Marketing/Course-Seller Hype Indicators (AUTO-REJECT)**
- "零基础" + "日入过千/月入过万" + "躺赚/全自动/无脑"
- "保姆级教程" / "扫码进群" / "领资料" / "私信我" / "V 我"
- Only peak revenue screenshot, no timeline, no failure mentions
- Author bio sells courses/consulting/community/"内部价"
- "知乎/小红书/抖音同名" — cross-platform course funnel
- Uses urgency: "名额仅剩 X 个" / "涨价倒计时" / "最后一期"

## Automation Tips

### RSSHub Feeds (for monitoring)
```
# Tieba forum monitoring
https://rsshub.app/tieba/forum/Linux吧
https://rsshub.app/tieba/forum/Kindle吧
https://rsshub.app/tieba/forum/开源软件吧

# Keyword search monitoring (if supported)
https://rsshub.app/tieba/keyword/GitHub/开源/求推荐
```

### TrendRadar / MediaCrawler Keywords
```
GitHub 开源 求推荐
批量下载 去水印 开源
贴吧 签到 云审核 开源
Kindle Calibre 推送 开源
Rime 雾凇 词库 开源
自托管 NAS Docker 开源
本地 AI Ollama Whisper 开源
```

### GitHub Project Tracking
- `star-history.com` — visualize star growth
- `github-weekly-rank` — weekly trending
- `github-trending` — daily trending
- Watch `Releases` + `Issues` for target projects
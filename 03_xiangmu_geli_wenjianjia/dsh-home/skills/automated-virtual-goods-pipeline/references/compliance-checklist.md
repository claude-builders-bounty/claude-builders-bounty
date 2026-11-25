# Compliance Checklist & Sensitive Word Evolution

## Platform Rule Change Log

| Date | Platform | Change | Impact on Pipeline |
|------|----------|--------|-------------------|
| 2024-04 | 闲鱼 | Virtual goods policy relaxed | Allowed "资料包/合集/素材库" terminology |
| 2024-08 | 闲鱼 | Crackdown on "课程/教程/培训班" keywords | Auto-replace mandatory |
| 2025-01 | 闲鱼 | "发车/拼团" free software fee | Use for high-volume accounts |
| 2025-06 | 闲鱼 | WebSocket protocol update (protobuf v2) | pyxianyu 1.0.0 required |
| 2026-03 | 闲鱼 | Single-device multi-account detection | ENFORE_SINGLE_ACCOUNT config |

## Sensitive Word Map (Living Config)

### Current `SENSITIVE_WORD_MAP` (v2026.09)

```json
{
  "课程": "资料包",
  "教程": "学习合集",
  "培训": "指导",
  "班": "期",
  "期": "季",
  "VIP": "尊享",
  "会员": "会员权益",
  "破解": "绿色版",
  "盗版": "非官方",
  "内部": "独家",
  "独家": "精选",
  "包过": "高通过率",
  "保过": "通过率高",
  "必过": "易通过",
  "100%": "高概率",
  "全网最": "优质",
  "第一": "头部",
  "限量": "限时",
  "绝版": "停更",
  "微信": "V信",
  "QQ": "扣扣",
  "群": "社群",
  "私聊": "站内信",
  "联系方式": "咨询方式",
  "百度网盘": "某盘",
  "网盘链接": "下载地址",
  "电子版": "数字版",
  "PDF版": "文档版",
  "视频教程": "视频资料",
  "音频课程": "音频资料",
  "直播回放": "录播资料",
  "录播": "回看",
  "加V": "加V信",
  "加微": "加V信",
  "主页": "个人页",
  "公众号": "公号",
  "知识星球": "星球",
  "星球": "社群",
  "社群": "圈子"
}
```

### Detection Rules

1. **Title scan**: All words in `SENSITIVE_WORD_MAP` keys → auto-replace before publish
2. **Description scan**: Same replacement + flag for manual review if >3 replacements
3. **Image OCR** (future): Check cover images for watermarked contact info
4. **Chat messages**: Auto-reply templates must not contain sensitive words

### Violation Response

| Violation Type | Detection | Auto-Action |
|----------------|-----------|-------------|
| Title contains sensitive word | Pre-publish check | Replace + log warning |
| Description >3 replacements | Pre-publish check | Block publish, require manual review |
| Chat message contains contact | Real-time monitor | Block send, use template reply |
| Image contains QR/WeChat | OCR (planned) | Flag for manual review |

## Account Safety Checklist

### New Account (0-30 days)
- [ ] Daily list limit: 5-10
- [ ] List interval: 60-180s
- [ ] No high-value items (>100元)
- [ ] Complete profile (avatar, bio, real-name verified)
- [ ] Bind phone + email + Alipay
- [ ] Browse/like/comment 3-5 days before first listing

### Warmed Account (30-90 days)
- [ ] Daily list limit: 10-20
- [ ] List interval: 30-120s
- [ ] Can test 50-100元 items
- [ ] Maintain 4.8+ rating
- [ ] Response rate >90% within 5min

### Mature Account (90+ days)
- [ ] Daily list limit: 20-50
- [ ] List interval: 15-60s
- [ ] Can use "发车/拼团" for fee waiver
- [ ] Multiple SKUs per item (3-5)
- [ ] Can run multiple categories

### Red Flags (Immediate Action)
- [ ] "风控拦截" in logs → Stop 24h, review sensitive words
- [ ] 403/429 errors >5/min → Backoff 1h, check IP/account
- [ ] Rating drop >0.2 in 24h → Audit recent deliveries
- [ ] Complaint rate >1% → Pause, review product quality

## Content Compliance

### Allowed Categories (Source Allowlist)
- ✅ GitHub Awesome lists (MIT/Apache/CC0 licenses)
- ✅ Government template libraries (gov.cn, samr.gov.cn)
- ✅ Official platform academies (小红书创作学院, 抖音创作者学院)
- ✅ Self-created original content
- ✅ CC0/公版 resources (Project Gutenberg, Unsplash, Pexels)

### Prohibited Categories (Hard Block)
- ❌ Paid course recordings (网课/训练营/大师课)
- ❌ Cracked software/license keys/activation tools
- ❌ Copyrighted video/movie/TV/anime/music
- ❌ Pirated books/novels/textbooks
- ❌ Brand logo/font/asset packs without license
- ❌ Exam answers/real test papers (考试真题/答案)
- ❌ Medical/legal/financial advice without license

### Gray Areas (Manual Review Required)
- ⚠️ "考公/考研/教资" real exam papers → Use only official published past papers
- ⚠️ "PPT/Excel/PS模板" from commercial sites → Verify license or recreate
- ⚠️ "脚本/工具/插件" from GitHub → Check license (GPL/AGPL = no commercial)
- ⚠️ "网盘资源合集" → Must be self-organized, not direct copy

## Delivery Compliance

### Channel Restrictions
- ✅ 发货凭证 (Order receipt) — Platform official channel
- ✅ 私聊 (Chat message) — Platform IM, no external links
- ❌ 微信/QQ/Email/外部链接 in any delivery message
- ❌ 二维码 in cover images or delivery content

### Message Templates (Pre-approved)
```text
亲，您拍的【{sku_name}】已发送网盘链接：{netdisk_url} 提取码：{netdisk_pwd} 请及时保存哦～
发货啦！{sku_name} 资料包已发网盘：{netdisk_url} 码：{netdisk_pwd} 有问题随时找我～
您好，{sku_name} 已发货：{netdisk_url} (提取码：{netdisk_pwd}) 资料持续更新，建议转存后查看～
```

### Card Code Rules
- One code per order (atomic reserve)
- Code format: alphanumeric, 16-32 chars, no confusing chars (0/O, 1/I/l)
- Delivery: Include in both receipt + chat
- Log: Record code hash (not plaintext) + order ID + timestamp

## Monitoring & Alerting

### Key Metrics to Track
| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Delivery success rate | >98% | 95-98% | <95% |
| Order processing latency | <30s | 30-60s | >60s |
| Sensitive word hits/day | <5 | 5-20 | >20 |
| Cookie 401 errors/day | 0 | 1-2 | >2 |
| Card inventory <20 | No | Yes | <10 |

### Alert Channels
- Feishu webhook (primary)
- DingTalk webhook (backup)
- Telegram bot (dev)
- Email (critical only)

## Audit Trail Requirements

Every action must log:
- Timestamp (ISO8601)
- Account ID
- Action type (search/list/publish/deliver/reply/polish)
- Target (item_id/order_id/buyer_id)
- Result (success/fail/retry)
- Error code/message if failed
- Sensitive word hits (if any)

Retention: 90 days minimum (GDPR/PIPL compliant)
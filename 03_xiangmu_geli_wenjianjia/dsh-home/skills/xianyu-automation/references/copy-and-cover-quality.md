# 商品素材质量：封面设计 + 文案风格

## 一、文案：不要写成“合规文档”

### 误例（AI 味浓，真实踩过）

```
【这份资料我做了什么】
网上能搜到零散的免费版本，但用起来费时费力。这份是我整理加工后的成品：
· 把 1 个来源、78 个文件整合成统一目录结构
· 生成可检索内容总览（00-内容总览.md）
· 编写原创使用指南（快速上手 + FAQ + 学习顺序）
【退款规则】依据《网络购买商品七日无理由退货暂行办法》第六条第三项……
```

问题：① 开头讲“我做了什么”，不是买家得到的 ② 列内部文件名（`00-内容总览.md`）
③ 引法条编号 ④ 无 emoji、无利益点。

### 真实竞品风格（实测）

```
【秒发】Excel/office/word/WPS办公插件表格
✨【全能办公助手】一次性拥有40+款专业插件，完美兼容Office和WPS全版本！
【店主寄语】一份资料，帮您少走弯路、节省时间
核心亮点：
✅ Excel神器套装：含E灵、方方格子等专业工具...
【发货时间】24小时自动发货
```

### 写作规则

| 规则 | 说明 |
|---|---|
| 利益点开头 | 第一句说「你能得到什么」，不说「我做了什么」 |
| emoji 分区 | `📊【标题】` `✨【我多做了这些】` `🎯【能用来做什么】` `🚀【发货】` `🛡️【售后承诺】` |
| **不露内部术语** | 禁止出现 `.md`/`.json` 文件名、`PROVENANCE`、`内容哈希`、`统一目录结构` |
| **法条只归档不进正文** | 法条编号存 `LEGAL_BASIS` 常量，正文只写「数字商品发出后不支持无理由退款」 |
| 用大白话 | 「拍下后自动秒发」而不是「发货时效：10分钟内」 |
| 保住合规闸门 | `validate_no_false_claims()` 必须继续拦编造数量/无依据背书/结果承诺 |

**关键：把内部实现翻译成买家利益**
```
❌ 内容哈希去重，剔除 4 个重复文件
✅ 逐个查重，帮你剔掉 4 个重复文件，不占空间

❌ 把 1 个来源、78 个文件整合成统一目录结构
✅ 78 个文件已按用途分好类，不用自己整理

❌ 生成可检索内容总览（00-内容总览.md）
✅ 附一份内容清单，想找哪个一眼就能定位
```

---

## 二、封面：用 Playwright + HTML/CSS，不要用扩散模型

### 为什么不用 AI 生图

1. **中文文字渲染不可靠** —— 生图模型的中文常乱码，而封面上的「78份」「永久有效」
   必须字字准确（错字 = 虚假宣传）
2. **买家要看「内容预览」不是「艺术图」** —— 数字资料高转化封面 = 信息图
   （大数字 + 卖点 + 保障徽章）
3. **零成本 + 确定性 + 可 A/B** —— 改字改色秒出图，不占 GPU

### 实现要点（`src/cover_designer.py`）

```python
# HTML/CSS 模板（渐变底 + 大数字 + 徽章）→ 浏览器截图
page = browser.new_page(viewport={"width":800,"height":800},
                        device_scale_factor=2)   # 2x = 1600px 高清
page.screenshot(path=out, type="jpeg", quality=92)
```

**排版公式**：`类目标签` → `大标题(自动缩字号)` → `超大数字(150px)` → `分隔线` →
`保障徽章` → `底部小字`。字号按标题长度降级：≤14字→56px，≤20字→46px，否则38px。

### ⚠️ 两个必踩的坑

**坑 1：asyncio 里不能用 Playwright **同步** API**
```
Error: It looks like you are using Playwright Sync API inside the asyncio loop.
```
`_prepare_images` 在协程链里被调 → 直接报错。
**修**：检测当前线程有无 running loop，有就丢到独立线程：
```python
try:
    asyncio.get_running_loop(); running = True
except RuntimeError:
    running = False
if running:
    with ThreadPoolExecutor(max_workers=1) as ex:
        path = ex.submit(_job).result(timeout=120)
else:
    path = _job()
```

**坑 2：封面标题要用“生成的商品标题”，不是来源标题**
`resource["title"]` 是 GitHub 仓库名（`awesome-excel/awesome-excel — Excel表格`），
印到封面上很丑。必须传 `display_title=`（如 `Excel表格合集78人事行政适用`）。

---

## 三、MCP 客户端两个硬伤（都会静默吞掉失败）

**硬伤 1：只判 `isError` 会漏掉业务层失败**
```json
{"isError": false,                                    ← 传输层成功
 "structuredContent": {"ok": false,                 ← 业务层失败！
   "error": {"error_type":"RateLimitedError", "retry_after":10.75},
   "message": "限流：bucket=item.write 每 60s 上限 1"}}
```
后果：上层报「发布返回成功但无 item_id」，**跳过限流重试**。
**修**：`success = not (isError or structuredContent.get("ok") is False)`；
并把 `message` + `retry_after` 拼进 `error` 串供上层退避重试。

**硬伤 2：StreamReader 默认 64KB 上限**
竞品长简介单行 JSON >64KB → `LimitOverrunError`。
**修**：`create_subprocess_exec(..., limit=10*1024*1024)`。

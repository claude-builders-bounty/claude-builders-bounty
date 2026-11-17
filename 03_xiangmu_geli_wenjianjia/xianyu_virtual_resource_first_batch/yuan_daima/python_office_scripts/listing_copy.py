#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详情页文案生成 —— 闲鱼风格（v2）

## v1 的问题（用户明确指出）

v1 按「合规优先」写，读起来像法律文书，AI 味浓：
  · 开头「【这份资料我做了什么】」—— 买家不关心你的心路历程
  · 列内部文件名（`00-内容总览.md`、`PROVENANCE.json`）—— 买家看不懂也不需要
  · 引用《网络购买商品七日无理由退货暂行办法》第六条第三项 —— 太说教
  · 没有 emoji、没有利益点、没有情绪

## 真实竞品长什么样（实测 3 个同行）

```
【秒发】Excel/office/word/WPS办公插件表格
✨【全能办公助手】一次性拥有40+款专业插件，完美兼容Office和WPS全版本！
【店主寄语】一份资料，帮您少走弯路、节省时间
核心亮点：
✅ Excel神器套装：含E灵、方方格子等专业工具...
【发货时间】24小时自动发货
```

特征：emoji 分区、**利益点开头**、具体到同类产品名、短段落、无内部术语。

## v2 原则（同时守住合规红线）

1. **利益点先行** —— 第一句说「你能得到什么」，不说「我做了什么」
2. **只写真数字** —— 数量必须是实测值（沿用 validate_no_false_claims 闸门）
3. **不露内部术语** —— 不出现 .md/.json 文件名、不出现法条编号
4. **保留保障信息** —— 发货/售后仍写清（降纠纷），但用大白话
5. **emoji 分区** —— 符合闲鱼阅读习惯

法条依据（我方内部记录，**不写进详情页**）：
  《网络购买商品七日无理由退货暂行办法》第六条第三项：
    在线下载的数字化商品不适用七日无理由退货。
  详情页只用买家能懂的口语（"数字商品发出后不支持无理由退款"）。
"""
# --- 迁移引导：把仓库根加入 sys.path（使 `from src.* import` 可用）---
import sys as _sys
from pathlib import Path as _Path
_here = _Path(__file__).resolve()
for _anc in _here.parents:
    if (_anc / "src" / "framework").is_dir():
        if str(_anc) not in _sys.path:
            _sys.path.insert(0, str(_anc))
        break
# --- 引导结束 ---

import re
from typing import Dict, List, Optional

# 文案生成器版本 —— 与 cover_designer.COVER_VERSION 一起写进发布登记表，
# 供 item_manager 识别「旧素材商品」下架重发。改文案风格必须 bump。
COPY_VERSION = "v2-xianyu-style"

# ---------------------------------------------------------------
# 内部合规依据（仅存档，不进详情页文案）
# ---------------------------------------------------------------
LEGAL_BASIS = {
    "regulation": "《网络购买商品七日无理由退货暂行办法》",
    "article_exclusion": "第六条第三项",
    "article_marking": "第二十条",
    "source": "https://www.gov.cn/zhengce/zhengceku/2020-11/03/content_5557118.htm",
    "verified_at": "2026-10-12",
    "quote": ("第六条：下列商品不适用七日无理由退货规定：……"
              "（三）在线下载或者消费者拆封的音像制品、计算机软件等数字化商品"),
}

# 类目 → 具体使用场景（让买家「看到自己」，比空泛的「提升效率」强）
USAGE_BY_CATEGORY = {
    "Excel表格": ["财务报表", "考勤统计", "工资核算", "进销存", "数据看板"],
    "速查表": ["写代码查语法", "命令速查", "快捷键对照", "面试复习"],
    "设计工具": ["平面设计", "UI 稿", "办公出图", "素材整理"],
    "免费素材": ["做 PPT 配图", "短视频封面", "公众号排版", "海报设计"],
    "精选清单": ["找资源", "技术选型", "系统学习路线"],
    "简历模板": ["应届求职", "跳槽转行", "校招社招"],
    "PPT模板": ["年终汇报", "毕业答辩", "项目路演", "教学课件"],
    "合同模板": ["租房合同", "劳动合同", "合作协议", "采购合同"],
    "考公资料": ["国考省考", "事业单位", "申论行测"],
}

# 类目 → 人群
AUDIENCE_BY_CATEGORY = {
    "Excel表格": ["财务", "人事", "行政", "运营", "想少做重复表的人"],
    "速查表": ["程序员", "运维", "在校学生", "转行学技术的人"],
    "设计工具": ["设计师", "运营美工", "个体店主", "自媒体"],
    "免费素材": ["自媒体博主", "运营", "小微商家", "学生"],
    "精选清单": ["想系统入门的人", "技术负责人", "爱收藏资源的人"],
    "简历模板": ["应届生", "职场人", "转行者", "管理层"],
    "PPT模板": ["职场汇报人", "毕业生", "讲师", "创业者"],
    "合同模板": ["租房族", "HR", "个体经营者", "小微企业主"],
    "考公资料": ["备考国考/省考的人", "事业单位考生"],
}

# 类目 emoji
CATEGORY_EMOJI = {
    "Excel表格": "📊", "速查表": "⚡", "设计工具": "🎨", "免费素材": "🖼️",
    "精选清单": "📚", "简历模板": "📄", "PPT模板": "📽️", "合同模板": "📝",
    "考公资料": "🎯",
}

# 这些策略描述会暴露内部实现，过滤掉
_INTERNAL_MARKERS = ("内容哈希", "哈希去重", "留痕", "PROVENANCE", "总览.md",
                     "00-内容总览", "统一目录结构", "INDEX.json")


def _count(pkg: Dict) -> Optional[int]:
    """取真实文件数（沿用 manifest 的实测统计）"""
    stats = pkg.get("stats") or {}
    v = stats.get("file_count")
    if isinstance(v, int) and v > 0:
        return v
    dv = pkg.get("delivery") or {}
    v = dv.get("file_count")
    if isinstance(v, int) and v > 0:
        return v
    for k in ("count", "resource_count", "total_files"):
        v = pkg.get(k)
        if isinstance(v, int) and v > 0:
            return v
    return None


def build_delivery_rules(pkg: Dict) -> str:
    """发货 + 售后 —— 大白话，不引法条编号"""
    mode = pkg.get("deliver_mode") or "网盘链接 + 提取码"
    return f"""🚀【发货】
· 拍下后自动秒发（在线时段即时处理）
· 发货形式：{mode}
· 订单页「发货凭证」和私聊都会发，注意查收
· 虚拟资料，无线下物流，不用等快递

🛡️【售后承诺】
· 链接失效 / 提取码错误 → 免费重发
· 文件损坏打不开 → 免费补发
· 内容和描述不符 → 协商补发或退款
有问题 48 小时内联系我，凭截图处理，绝不推诿

💡【拍前须知】
数字商品发出后不支持无理由退款，介意勿拍~
先私聊确认符合需求再下单，对双方都好 🙏"""


def build_description(pkg: Dict, diff: Optional[Dict] = None) -> str:
    """生成闲鱼风格详情页

    pkg: title / category / items / audience / license_key / stats / delivery
    diff: 差异化加工记录（用于写实打实的卖点）
    """
    diff = diff or {}
    title = str(pkg.get("title") or "数字资料包")
    category = str(pkg.get("category") or "资料")
    n = _count(pkg)
    emoji = CATEGORY_EMOJI.get(category, "📦")

    parts: List[str] = []

    # ── 1. 开头：利益点（不是「我做了什么」）─────────────────────
    parts.append(f"{emoji}【{title}】")
    parts.append("")

    if n:
        parts.append(f"整理好的 {n} 份资源，目录已分类，下载即用 —— "
                     f"省去自己一个个找、一个个下、一个个改名的功夫。")
    else:
        parts.append("整理好的资源包，目录已分类，下载即用 —— "
                     "省去自己一个个找、一个个下、一个个改名的功夫。")
    parts.append("")

    # ── 2. 亮点（具体、可验证；过滤暴露内部实现的描述）─────────
    strategies = diff.get("strategies") or []
    parts.append("✨【我多做了这些】")
    shown = 0
    for s in strategies:
        s = str(s).strip()
        if not s or any(k in s for k in _INTERNAL_MARKERS):
            continue
        if shown >= 2:
            break
        parts.append(f"· {s}")
        shown += 1
    parts.append("· 附一份使用指南，拿到手知道怎么用、怎么改")
    parts.append("· 附来源与授权说明，用着放心")
    parts.append("")

    # ── 3. 适用场景（让买家「看到自己」）────────────────────────
    usages = USAGE_BY_CATEGORY.get(category)
    if usages:
        parts.append("🎯【能用来做什么】")
        parts.append(" / ".join(usages))
        parts.append("")

    # ── 4. 适合谁 ──────────────────────────────────────────
    audience = pkg.get("audience") or AUDIENCE_BY_CATEGORY.get(category)
    if audience:
        parts.append("👥【适合谁】")
        parts.append("、".join(audience))
        parts.append("")

    # ── 5. 发货 + 售后 ────────────────────────────────────
    parts.append(build_delivery_rules(pkg))
    parts.append("")

    # ── 6. 授权说明（一句话，不列文件）─────────────────────────
    lic = str(pkg.get("license_key") or "").strip()
    if lic:
        commercial = "、可商用" if lic.upper() in (
            "MIT", "APACHE-2.0", "CC0-1.0", "BSD-3-CLAUSE", "BSD-2-CLAUSE") else ""
        parts.append(f"📜 原始素材为 {lic} 许可{commercial}，署名与许可原文随包提供。")

    return "\n".join(parts)


# ---------------------------------------------------------------
# 合规自检（保留 v1 闸门，防止编造数量）
# ---------------------------------------------------------------
def _verified_counts(pkg: Dict) -> set:
    """收集被证据支撑的真实数字 —— 只有这些允许出现在文案里"""
    ok = {len(pkg.get("items") or [])}
    stats = pkg.get("stats") or {}
    for k in ("file_count", "source_count", "dedupe_dropped", "total_bytes"):
        v = stats.get(k)
        if isinstance(v, int):
            ok.add(v)
    for v in (pkg.get("verified_counts") or []):
        if isinstance(v, int):
            ok.add(v)
    n = _count(pkg)
    if n:
        ok.add(n)
    ok.discard(0)
    return ok


def validate_no_false_claims(text: str, pkg: Dict) -> List[str]:
    """合规自检 —— 返回问题列表（空 = 通过）

    红线：
      1. 「共 N 套/份/个」的数量必须在【已验证真实数字】集合内（禁止编造 888 套）
      2. 禁止「正版授权」「官方合作」等无依据背书
      3. 禁止「包过」「包学会」等结果性承诺
    """
    problems: List[str] = []

    CN_NUM = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
              "七": 7, "八": 8, "九": 9, "十": 10, "百": 100, "千": 1000,
              "万": 10000, "两": 2}
    CN_UNITS = {"十": 10, "百": 100, "千": 1000, "万": 10000}

    def parse_cn_number(s: str) -> Optional[int]:
        if not s:
            return None
        if all(ch in CN_NUM or ch in CN_UNITS for ch in s):
            total = 0
            current = 0
            for ch in s:
                if ch in CN_UNITS:
                    unit = CN_UNITS[ch]
                    if current == 0:
                        current = 1
                    total += current * unit
                    current = 0
                else:
                    current = current * 10 + CN_NUM[ch]
            total += current
            return total
        return None

    def normalize_number_str(s: str) -> Optional[int]:
        s = s.strip()
        if not s:
            return None
        s = s.translate(str.maketrans("０１２３４５６７８９，", "0123456789,"))
        s = s.replace(",", "")
        if s.isdigit():
            return int(s)
        return parse_cn_number(s)

    TOTAL_CLAIM_RE = re.compile(
        r"(?:共|总计|全套|一共|总计有|包含)\s*([\d一-鿿,０-９]+)\s*[套份个]"
        r"|([\d一-鿿,０-９]+)\s*[套份个](?:资料|资源|模板|合集|大礼包|素材|课程|教程)"
    )

    verified = _verified_counts(pkg)
    for m in TOTAL_CLAIM_RE.finditer(text):
        raw = m.group(1) or m.group(2)
        claimed = normalize_number_str(raw)
        if claimed is not None and claimed not in verified:
            problems.append(
                f"疑似编造总数：「{m.group(0).strip()}」不在已验证真实数字集合 "
                f"{sorted(verified)} 内")

    for word in ("正版授权", "官方合作", "官方授权", "独家授权"):
        if word in text:
            problems.append(f"无依据背书：「{word}」—— 除非能出示授权证明，否则删除")

    for word in ("包过", "包学会", "保证通过", "稳赚", "必过"):
        if word in text:
            problems.append(f"结果性承诺：「{word}」—— 属虚假宣传，必须删除")

    SPECIFIC_CLAIM_RE = re.compile(
        r"(?:共|包含|含|内含|附带)\s*([\d一-鿿,０-９]+)\s*(?:页|张|个|份|MB|GB|KB|分钟|小时|秒)"
    )
    for m in SPECIFIC_CLAIM_RE.finditer(text):
        raw = m.group(1)
        claimed = normalize_number_str(raw)
        if claimed is not None and claimed not in verified:
            problems.append(
                f"疑似编造具体数字：「{m.group(0).strip()}」不在已验证真实数字集合 "
                f"{sorted(verified)} 内")

    return problems


if __name__ == "__main__":
    pkg = {
        "title": "Excel表格合集78人事行政适用",
        "category": "Excel表格",
        "items": ["内容总览", "使用指南", "资料文件 78 个", "授权说明"],
        "stats": {"file_count": 78, "source_count": 1},
        "license_key": "MIT",
        "delivery": {"file_count": 78},
    }
    diff = {"strategies": ["把 1 个来源、78 个文件整合成统一目录结构",
                           "内容哈希去重，剔除 4 个重复文件",
                           "生成可检索内容总览（00-内容总览.md）"]}
    text = build_description(pkg, diff)
    print(text)
    print("\n" + "=" * 60)
    print(f"字数：{len(text)}")
    print("合规自检：", validate_no_false_claims(text, pkg) or "✅ 通过")

    print("\n=== 反例自检（应当被拦下）===")
    bad = "本资料共 888 套，正版授权，包过！"
    for p in validate_no_false_claims(bad, pkg):
        print("  ⛔", p)

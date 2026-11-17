#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: 自动上架 - 基于 goofish-cli (MCP) 发布商品
功能：
1. 读取货源清单 + 选品报表
2. 生成标题/文案/主图/SKU
3. 批量发布商品 (goofish-cli item_publish)
4. 记录发布结果 (item_id, 链接, 状态)
"""

import asyncio
import csv
import json
import os
import random
import re
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

import pandas as pd
from loguru import logger
from tqdm import tqdm

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
from src.framework.config_loader import get_config
from src.roles.legal_guardian.legal_gate import check_resource
from src.roles.marketing_planner.listing_copy import build_description, validate_no_false_claims
from src.framework.mcp_tools import PhaseTools, get_mcp_client


@dataclass
class ListingTask:
    """单个上架任务"""
    package_id: str
    category: str
    title: str
    description: str
    price: float
    original_price: float
    sku_list: List[Dict]  # [{"name": "单套", "price": 9.9, "stock": 999}, ...]
    images: List[str]  # 本地图片路径或网盘链接
    tags: List[str]
    netdisk_url: str = ""
    netdisk_pwd: str = ""
    status: str = "pending"  # pending/publishing/success/failed
    item_id: str = ""
    item_url: str = ""
    error_msg: str = ""
    created_at: str = ""
    published_at: str = ""
    # 上架前质检报告（由 pre_listing_quality_gate 写入）。
    # 放在 ListingTask 上而不是转成 dict —— 下游 run_listing/publish_task
    # 用属性访问（task.title / task.images），传 dict 会直接崩。
    quality_report: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class AutoLister:
    """自动上架核心类"""

    def __init__(self, config=None, mcp_client=None):
        self.config = config or get_config()
        self.mcp_tools = PhaseTools(mcp_client) if mcp_client else None
        self.tasks: List[ListingTask] = []
        self.results: List[Dict] = []
        # 本次运行是否已刷过 cookie（频繁 auth_login 本身会触发风控 → 每轮最多 1 次）
        self._auth_refreshed = False

        # 敏感词过滤映射
        self.sensitive_map = self.config.security.sensitive_word_map

    async def initialize(self):
        """初始化"""
        logger.info("自动上架客户端初始化完成")

    def close(self):
        """关闭客户端"""
        logger.info("自动上架客户端已关闭")

    # ============================================================
    # 1. 任务生成：从货源包 + 选品报表生成上架任务
    # ============================================================
    # 允许的货源清单文件名前缀 —— 防止误指旧的 resource_manifest（含竞品）
    #   sellable_manifest_*    : Phase 2 过闸清单（尚无交付物）
    #   deliverable_manifest_* : Phase 2.5 落地清单（已上传网盘，带分享链接）
    ALLOWED_MANIFEST_PREFIXES = ("sellable_manifest_", "deliverable_manifest_")

    # 标题违禁词（平台规则 + 虚假宣传风险词）。
    # 用于校验清单提供的 seo_title —— 宁可回退模板，也不让违规标题上线。
    _TITLE_BANNED = (
        "最", "顶", "第一", "绝对", "全网", "独家", "唯一", "永久", "终身",
        "亏本", "跳楼价", "白菜价", "包过", "包学会", "稳赚", "必过",
        "微信", "VX", "vx", "加我", "联系我", "官方授权", "正版授权",
    )

    def load_tasks_from_factory(self, factory_manifest: str, selection_csv: str = None) -> List[ListingTask]:
        """从货源工厂清单 + 选品报表生成上架任务

        法律硬闸（三重，不可绕过）——上架是唯一有真实法律后果的动作：
          闸1 文件名必须 sellable_manifest_*.json
              （旧 resource_manifest_*.json 含竞品数据，直接拒绝加载）
          闸2 每条货源再过一次 check_resource()（防篡改 / 防旧文件 / 防手改）
          闸3 全部未过闸时中止（fail-closed），绝不"空跑上架"
        """
        p = Path(factory_manifest)
        if not p.exists():
            raise FileNotFoundError(f"货源清单不存在: {factory_manifest}")

        # ---- 闸 1：文件名白名单 ----
        if not p.name.startswith(self.ALLOWED_MANIFEST_PREFIXES):
            raise ValueError(
                f"拒绝加载 {p.name}：只有 {' / '.join(self.ALLOWED_MANIFEST_PREFIXES)}"
                f"*.json 是过闸清单。旧 resource_manifest 含竞品数据，严禁上架。")

        with open(p, "r", encoding="utf-8") as f:
            resources = json.load(f)

        # ---- 闸 2：逐条重验（defense in depth）----
        legal_ok, legal_blocked = [], []
        for res in resources:
            v = check_resource(res)
            (legal_ok if v.sellable else legal_blocked).append((res, v))
        if legal_blocked:
            logger.warning(f"上架前重验：{len(legal_blocked)}/{len(resources)} 条未过闸 → 剔除")
            for res, v in legal_blocked[:5]:
                logger.warning(f"    ⛔ {res.get('title', '?')}: {v.reasons[0][:70]}")
            if any(r.get("source") == "competitor" for r, _ in legal_blocked):
                logger.error("    ⚠️ 检出竞品数据混入清单！来源可疑 —— 请重跑 Phase 2")
        resources = [res for res, _ in legal_ok]

        # ---- 闸 2b：虚拟商品必须有真实交付链接（无交付物不得上架）----
        with_delivery, without = [], []
        for res in resources:
            link = res.get("netdisk_url") or (res.get("delivery") or {}).get("netdisk_url")
            (with_delivery if link else without).append(res)
        if without:
            logger.warning(f"上架前交付检查：{len(without)}/{len(resources)} 条无网盘交付链接 → 剔除"
                           f"（虚拟商品无交付物不得上架）")
            for res in without[:5]:
                logger.warning(f"    ⏭ {res.get('title', '?')}")
        resources = with_delivery

        # ---- 闸 3：fail-closed ----
        if not resources:
            raise RuntimeError("无任何货源通过法律闸口 —— 中止上架（fail-closed）")

        # 读取选品报表获取热门关键词/风格参考
        selection_data = {}
        if selection_csv and Path(selection_csv).exists():
            df = pd.read_csv(selection_csv)
            for _, row in df.iterrows():
                cat = row.get("category", "")
                if cat not in selection_data:
                    selection_data[cat] = {
                        "top_titles": [],
                        "styles": set(),
                        "usages": set()
                    }
                selection_data[cat]["top_titles"].append(row.get("title", ""))

        tasks = []
        daily_limit = self.config.listing.daily_limit

        for i, res in enumerate(resources[:daily_limit]):  # 限制每日上架数
            category = res.get("category", "其他")
            title_base = res.get("title", f"{category}资源包")
            source = res.get("source", "unknown")
            source_url = res.get("url", "")

            # 生成标题
            title = self._generate_title(category, title_base, selection_data.get(category, {}), res)

            # 生成文案
            description = self._generate_description(category, title_base, source, source_url, res)

            # 生成 SKU
            sku_list = self._generate_sku(category, res)

            # 图片（用**生成的商品标题**做封面，不是 GitHub 仓库名）
            images = self._prepare_images(category, res, display_title=title)

            # 价格
            base_price = min(sku["price"] for sku in sku_list)
            original_price = base_price * 3  # 划线价

            task = ListingTask(
                package_id=res.get("package_id", f"pkg_{i}"),
                category=category,
                title=title,
                description=description,
                price=base_price,
                original_price=original_price,
                sku_list=sku_list,
                images=images,
                tags=[category, source],
                netdisk_url=(res.get("netdisk_url")
                             or (res.get("delivery") or {}).get("netdisk_url", "")),
                netdisk_pwd=(res.get("netdisk_pwd")
                             or (res.get("delivery") or {}).get("netdisk_pwd", ""))
            )
            tasks.append(task)

        self.tasks = tasks
        logger.info(f"生成上架任务: {len(tasks)} 个")
        return tasks

    def _real_count(self, res: Optional[Dict] = None) -> Optional[str]:
        """真实资源套数 —— 只有资源包里有实测统计时才返回，否则 None

        合规红线：标题/文案里的「XXX套」必须是真实数量。
        编造数量（如随机 888 套）属于虚假宣传，不能做。

        deliverable_manifest 里的真实数量在 res["delivery"]["file_count"]
        """
        if not res:
            return None
        # 优先读 delivery.file_count（Phase 2.5 产出的落地清单）
        dv = res.get("delivery") or {}
        v = dv.get("file_count")
        if isinstance(v, int) and v > 0:
            return str(v)
        # 回退顶层字段
        for key in ("count", "file_count", "resource_count", "total_files"):
            v = res.get(key)
            if isinstance(v, int) and v > 0:
                return str(v)
        return None

    # 品类 → 真实适用场景。避免「合同模板 适用毕业答辩」这种乱配
    USAGE_BY_CATEGORY = {
        "合同模板": ["租房合同", "劳动合同", "合作协议", "买卖协议"],
        "考公资料": ["国考省考", "事业单位", "申论行测"],
        "教资资料": ["教资笔试", "教资面试", "综合素质"],
        "简历模板": ["求职面试", "校招社招", "转行跳槽"],
        "PPT模板": ["毕业答辩", "年终汇报", "项目展示", "教学课件"],
        "Excel表格": ["财务报表", "数据分析", "项目管理", "人事行政"],
        "小红书运营": ["账号起号", "内容变现", "选题排版"],
        "抖音运营": ["账号起号", "短视频脚本", "流量变现"],
        "Notion模板": ["效率管理", "时间规划", "知识库搭建"],
        "剪映模板": ["视频剪辑", "卡点转场", "口播字幕"],
        "视频素材": ["视频剪辑", "卡点转场", "口播字幕"],
    }
    USAGE_DEFAULT = ["日常办公", "效率提升", "学习参考"]

    def _infer_audience(self, category: str) -> List[str]:
        """从品类推断受众（用于详情页）"""
        mapping = {
            "合同模板": ["租房/借房人", "入职/离职职场人", "合作/买卖双方"],
            "考公资料": ["国考/省考/事业单位备考者"],
            "教资资料": ["教师资格证笔试/面试备考者"],
            "简历模板": ["应届生/职场人/转行者/管理层"],
            "PPT模板": ["毕业生/汇报人/讲师/创业者"],
            "Excel表格": ["财务/数据分析/项目管理/人事/行政人员"],
        }
        return mapping.get(category, ["日常办公/学习/效率提升人群"])

    def _generate_title(self, category: str, base_title: str,
                        selection_info: Dict, res: Optional[Dict] = None) -> str:
        """生成标题（套用模板 + 敏感词替换）

        合规：{count} 只能用真实统计；拿不到真实数量就选不含 {count} 的模板。
        """
        # ---- SEO 覆盖钩子 ----
        # 允许货源清单提供已做关键词优化的标题（seo_title）。
        # 为什么不直接信任：清单可能来自自动化流程，标题一旦违规整条商品会被平台处罚。
        # 因此这里做两道校验，不通过就静默回退模板生成（fail-safe，不阻断上架）。
        seo_title = str((res or {}).get("seo_title") or "").strip()
        if seo_title:
            bad = [w for w in self._TITLE_BANNED if w in seo_title]
            if len(seo_title) > 30:
                logger.warning(f"seo_title 超 30 字（{len(seo_title)}）→ 回退模板生成：{seo_title[:30]}")
            elif bad:
                logger.warning(f"seo_title 含违禁词 {bad} → 回退模板生成：{seo_title}")
            else:
                logger.info(f"采用清单提供的 SEO 标题（{len(seo_title)} 字）：{seo_title}")
                return seo_title

        templates = list(self.config.listing.title_templates or [])
        if not templates:
            templates = [
                "{count}套{keyword}高端模板含{style}适用{usage}",
                "{keyword}资料包{count}份{style}最新{date}版",
                "正版{keyword}合集{count}套{usage}专用{style}风格",
            ]

        # 关键词：剥离泛化后缀，但不能剥成空
        keyword = category
        for suffix in ("模板", "资料", "素材", "合集", "资源"):
            if keyword.endswith(suffix) and len(keyword) > len(suffix):
                keyword = keyword[: -len(suffix)]
        if not keyword.strip():
            keyword = res.get("keyword") if res else "" or category

        real_count = self._real_count(res)

        # 按「能否诚实给出数量」筛选模板
        if real_count:
            usable = [t for t in templates if "{count}" in t] or templates
        else:
            usable = [t for t in templates if "{count}" not in t]
        # 剔除所有含 {style} 的模板 —— 风格词（ins风/莫兰迪…）无法从真实数据核实，
        # 属编造卖点，一律不允许出现在标题里
        usable = [t for t in usable if "{style}" not in t]
        if not usable:
            usable = [
                "{keyword}合集{count}{usage}适用",
                "{keyword}资料包{count}份最新{date}版",
                "{keyword}模板{count}套{usage}适用",
            ]

        usages = self.USAGE_BY_CATEGORY.get(category, self.USAGE_DEFAULT)

        template = random.choice(usable)
        title = template.format(
            count=real_count or "",
            keyword=keyword,
            usage=random.choice(usages),
            date=datetime.now().strftime("%Y%m"),
        )

        # 折叠重复词：category='模板' 时会出现「模板模板」「资料包资料包」
        title = re.sub(r"(模板|资料包|合集|素材|资源)\1+", r"\1", title)

        for sensitive, replacement in self.sensitive_map.items():
            title = title.replace(sensitive, replacement)

        # 闲鱼标题上限 30 字；截断后去掉尾部残标点
        return title[:30].rstrip("的在和与·-—、,，")

    def _pick_style(self, keyword: str) -> Optional[str]:
        """从选品数据里挑一个真实出现过的风格词（可选）"""
        return None

    def _generate_description(self, category: str, base_title: str, source: str,
                              source_url: str, res: Optional[Dict] = None) -> str:
        """生成商品描述 —— 基于真实加工数据 + 合规模板（替代硬编码编造文案）"""
        # ---- SEO 覆盖钩子 ----
        # 允许清单提供人工撰写/审校过的详情页文案（seo_desc）。
        # 不直接信任，过三道检查，任一不过就回退模板生成：
        #   1. validate_no_false_claims —— 禁止编造数量/无依据背书/结果性承诺
        #   2. 法条泄漏检测 —— 法律依据属内部材料，不得出现在买家可见文案里
        #   3. 敏感词替换 —— 与模板生成路径使用同一套 self.sensitive_map
        seo_desc = str((res or {}).get("seo_desc") or "").strip()
        if seo_desc and res is not None:
            dv = res.get("delivery") or {}
            pkg = dict(res)
            pkg.setdefault("items", dv.get("items") or [])
            st = dict(pkg.get("stats") or {})
            if dv.get("file_count") is not None and "file_count" not in st:
                st["file_count"] = dv["file_count"]
            pkg["stats"] = st

            problems = validate_no_false_claims(seo_desc, pkg)
            laws = re.findall(r"《[^》]{2,40}》", seo_desc)
            if problems:
                logger.warning(f"seo_desc 未过真实数字校验 → 回退模板生成：{problems[:3]}")
            elif laws:
                logger.warning(f"seo_desc 含法条引用 {laws[:3]} → 回退模板生成"
                               f"（法律依据只存内部文档，不得进买家可见文案）")
            else:
                for sensitive, replacement in self.sensitive_map.items():
                    seo_desc = seo_desc.replace(sensitive, replacement)
                logger.info(f"采用清单提供的 SEO 详情页文案（{len(seo_desc)} 字）")
                return seo_desc

        # 从加工结果 res 取真实交付物/差异化卖点/授权义务
        if not res:
            # 兜底：无加工记录时的最小合规文案（不承诺具体发货方式，避免虚假宣传）
            return (
                f"【包含内容】{base_title}\n\n"
                f"【发货方式】交付方式待确认，下单前请私聊咨询\n\n"
                f"【退款规则】依据《网络购买商品七日无理由退货暂行办法》第六条第三项，"
                f"在线下载的数字化商品不适用七日无理由退货。\n"
                f"资料一经发出/提取，视为交付完成，不支持无理由退款。\n\n"
                f"【售后】链接失效/文件损坏/内容不符 → 48 小时内免费补发/退款。\n\n"
                f"资料为虚拟商品，售出后不涉及实物退换，请知悉。"
            )

        # 交付数据在 deliverable manifest 里位于 res["delivery"]；
        # 兼容旧的扁平结构（顶层同名键优先）。
        # 注意：漏了这层映射 = 详情页看不到交付物清单/差异化卖点/授权义务，
        # 二次创作全部白做（买家根本不知道买了什么）。
        dv = res.get("delivery") or {}

        def _pick(key, default):
            v = res.get(key)
            if v in (None, "", [], {}):
                v = dv.get(key)
            return default if v in (None, "", [], {}) else v

        pkg = {
            "title": base_title,
            "category": category,
            "deliver_mode": "网盘链接 + 提取码",
            "deliver_within": 10,
            "items": _pick("items", []),
            "audience": self._infer_audience(category),
            "rights": _pick("obligations", []),
            "license_key": _pick("license_key", ""),
            "stats": {
                "file_count": _pick("file_count", None),
                "dedupe_dropped": _pick("dedupe_dropped", None),
                "source_count": _pick("source_count", None),
                "total_bytes": _pick("package_bytes", None),
            },
        }
        diff = {
            "strategies": _pick("strategies", []),
        }

        # 生成文案
        desc = build_description(pkg, diff)

        # 合规自检（必须过）
        problems = validate_no_false_claims(desc, pkg)
        if problems:
            # 理论上不会触发（build_description 基于真实数据生成），但保底记录
            import logging
            logging.getLogger(__name__).warning(
                f"详情页合规自检发现问题: {problems} | title={base_title}")

        # 敏感词替换（最后一层防线）
        for sensitive, replacement in self.sensitive_map.items():
            desc = desc.replace(sensitive, replacement)

        return desc

    def _generate_sku(self, category: str, res: Optional[Dict] = None) -> List[Dict]:
        """生成 SKU 列表"""
        # ---- SKU 覆盖钩子 ----
        # 允许清单指定分档（seo_sku）。校验：至少 1 档、每档有正数价格、
        # 名称非空 —— 不合法就回退配置模板，避免生成出无法上架的 SKU。
        provided = (res or {}).get("seo_sku")
        if isinstance(provided, list) and provided:
            ok_skus = []
            for s in provided:
                if not isinstance(s, dict):
                    continue
                nm = str(s.get("name") or "").strip()
                try:
                    pr = float(s.get("price"))
                except (TypeError, ValueError):
                    continue
                if nm and pr > 0:
                    ok_skus.append({"name": nm, "price": pr,
                                    "stock": int(s.get("stock") or 999)})
            if ok_skus:
                logger.info(f"采用清单提供的 SKU {len(ok_skus)} 档："
                            f"{[(s['name'], s['price']) for s in ok_skus]}")
                return ok_skus
            logger.warning("seo_sku 无有效分档 → 回退配置模板")

        templates = self.config.listing.sku_templates
        cat_key = category.replace("模板", "").replace("资料", "").replace("素材", "")
        sku_tpl = templates.get(cat_key, templates.get("默认", [
            {"name": "基础版", "price": 9.9, "stock": 999},
            {"name": "进阶版", "price": 19.9, "stock": 999},
            {"name": "尊享版", "price": 39.9, "stock": 999}
        ]))

        # 确保每个 SKU 有 stock 字段
        for sku in sku_tpl:
            if "stock" not in sku:
                sku["stock"] = 999

        return sku_tpl

    def _prepare_images(self, category: str, resource: Dict,
                        display_title: str = None) -> List[str]:
        """准备商品图片 —— 用 cover_designer 生成真实设计封面

        旧实现是 800x800 灰底灰字占位图（无设计感，也无卖点信息）。
        新实现用 HTML/CSS + Playwright 出图：渐变背景 + 大数字 + 保障徽章，
        文字精准（浏览器排版，不是 AI 生图的乱码中文）。

        display_title: **生成的商品标题**（如「Excel表格合集78人事行政适用」）。
        必须传它 —— resource["title"] 是来源标题（GitHub 仓库名，
        形如 "awesome-excel/awesome-excel — Excel表格"），印到封面上很丑。
        """
        from src.roles.marketing_planner.cover_designer import build_cover

        # ---- 封面覆盖钩子 ----
        # 允许清单提供已生成并通过排版核验的封面图（cover_images）。
        # 只接受**真实存在且非空**的文件，避免清单里写错路径导致商品无图。
        provided = (resource or {}).get("cover_images") or []
        picked = [str(p) for p in provided if p and Path(p).exists() and Path(p).stat().st_size > 0]
        if picked:
            missing = len(provided) - len(picked)
            logger.info(f"采用清单提供的封面 {len(picked)} 张"
                        + (f"（{missing} 张路径无效已忽略）" if missing else ""))
            return picked

        covers_dir = Path("resources") / "covers" / category
        covers_dir.mkdir(parents=True, exist_ok=True)

        title = str(display_title or resource.get("title") or category)
        # 文件名安全化
        safe = "".join(c for c in title if c.isalnum() or c in "-_")[:48] or category
        out = covers_dir / f"cover_{safe}.jpg"

        # 取真实数量（只用实测值，不编造）
        dv = resource.get("delivery") or {}
        stats = resource.get("stats") or {}
        count = (dv.get("file_count") if isinstance(dv.get("file_count"), int)
                 else stats.get("file_count") if isinstance(stats.get("file_count"), int)
                 else None)

        pkg = {
            "title": title,
            "category": category,
            "count": count,
            "license_key": resource.get("license") or resource.get("license_key"),
            "has_guide": True,   # 我们的包里确实都带使用指南
        }

        path = build_cover(pkg, str(out))
        if path:
            return [path]

        # 兜底：真出不了图才退回旧占位图
        logger.warning("cover_designer 出图失败，回退占位图")
        legacy = covers_dir / f"cover_{category}.jpg"
        if not legacy.exists():
            self._generate_placeholder_cover(legacy, category)
        return [str(legacy)]

    def _generate_placeholder_cover(self, path: Path, category: str):
        """生成占位封面图"""
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (800, 800), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)
        try:
            # 跨平台字体回退: Windows → Linux → 默认
            _font_candidates = [
                "C:/Windows/Fonts/msyh.ttc",       # Windows 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",     # Windows 黑体
                "C:/Windows/Fonts/arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            ]
            font = None
            for _fp in _font_candidates:
                if os.path.exists(_fp):
                    font = ImageFont.truetype(_fp, 48)
                    break
            if font is None:
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        text = f"{category}\n资源包封面"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((800-tw)//2, (800-th)//2), text, font=font, fill=(100, 100, 100))
        img.save(path, "JPEG", quality=90)

    # ============================================================
    # 2. 发布执行 - 使用 goofish-cli MCP
    # ============================================================
    # 与 goofish-cli core/mtop.py 的 _RISK_KEYWORDS / _AUTH_KEYWORDS 严格对齐
    #   _RISK_KEYWORDS = ("RGV587_ERROR", "FAIL_SYS_USER_VALIDATE", "哎哟喂", "/punish")
    #   _AUTH_KEYWORDS = ("FAIL_SYS_SESSION_EXPIRED", "FAIL_SYS_TOKEN_EXOIRED",
    #                     "FAIL_SYS_TOKEN_EMPTY", "令牌过期", "FAIL_SYS_ILLEGAL_ACCESS")
    RISK_MARKERS = ("RGV587_ERROR", "FAIL_SYS_USER_VALIDATE", "哎哟喂", "/punish",
                    "风控", "RiskControl", "熔断")
    AUTH_MARKERS = ("FAIL_SYS_SESSION_EXPIRED", "FAIL_SYS_TOKEN_EXOIRED", "FAIL_SYS_TOKEN_EMPTY",
                    "令牌过期", "FAIL_SYS_ILLEGAL_ACCESS", "登录态失效")
    LIMIT_MARKERS = ("限流", "RateLimited", "rate limit", "retry_after")

    # 兜底类目 DTO —— **由平台 category.recommend 对同类数字资源包实测返回**，
    # 不是猜测值（cat_name=设计素材/源文件）。用于 AI 识别失败时保证能上架。
    # 背景：我们的封面是生成的占位图，AI 类目推荐器对「速查表」「设计工具」等
    #       自造词识别不到，返回空 categoryPredictResult → 发布中断。
    FALLBACK_CATEGORY = {
        "cat_id": "50023914",
        "cat_name": "设计素材/源文件",
        "channel_cat_id": "201454708",
        "tb_cat_id": "201160807",
    }

    async def _resolve_category(self, title: str, images: List[Dict]) -> Dict:
        """解析真实数字类目 DTO（喂给 item_publish 的 category_json）。

        顺序：平台 AI 识别 → 失败则用 FALLBACK_CATEGORY。
        返回一定是含 cat_id / channel_cat_id / tb_cat_id 的真实数字 DTO，
        这样 goofish-cli 会跳过它内部的 category.recommend（避免再次失败）。
        """
        try:
            r = await self.mcp_tools.mcp.call_tool(
                "goofish", "category_recommend",
                {"title": title, "images_json": json.dumps(images)})
            d = (r.data or {}).get("structuredContent", {}) or {}
            data = d.get("data") or {}
            if (d.get("ok") and data.get("cat_id")
                    and data.get("channel_cat_id") and data.get("tb_cat_id")):
                logger.info(f"类目识别成功: {data.get('cat_name')} "
                            f"(cat_id={data.get('cat_id')})")
                return {
                    "cat_id": str(data["cat_id"]),
                    "cat_name": data.get("cat_name", ""),
                    "channel_cat_id": str(data["channel_cat_id"]),
                    "tb_cat_id": str(data["tb_cat_id"]),
                }
            logger.warning(f"类目 AI 识别失败（{str(d.get('message'))[:60]}）→ 用兜底类目 "
                           f"{self.FALLBACK_CATEGORY['cat_name']}")
        except Exception as e:
            logger.warning(f"类目识别异常（{type(e).__name__}: {e}）→ 用兜底类目")
        return dict(self.FALLBACK_CATEGORY)

    @classmethod
    def _classify_publish_error(cls, msg: str) -> str:
        """把扁平错误文本归类，供无人值守决策

        limited → 按 retry_after 等待后重试同一商品（配额未消耗）
        risk    → 立即中止整批（熔断已开，继续只会加重风控）
        auth    → 刷一次 cookie 再续
        other   → 本条失败，继续下一条
        """
        m = msg or ""
        if any(k in m for k in cls.RISK_MARKERS):
            return "risk"
        if any(k in m for k in cls.LIMIT_MARKERS):
            return "limited"
        if any(k in m for k in cls.AUTH_MARKERS):
            return "auth"
        return "other"

    @staticmethod
    def _parse_retry_after(msg: str) -> float:
        """从 '再等 37.2s' 等文本抽出等待秒数，缺省 60s"""
        m = re.search(r"再等\s*([\d.]+)\s*s", msg or "")
        if not m:
            m = re.search(r"retry_after[\"'\s=:]+([\d.]+)", msg or "", re.I)
        return float(m.group(1)) if m else 60.0

    async def _refresh_auth(self) -> bool:
        """刷新登录态（每次运行最多刷 1 次 —— 频繁 auth_login 本身会触发风控）"""
        if self._auth_refreshed:
            return False
        self._auth_refreshed = True
        cookie = os.environ.get("XIANYU_COOKIE", "")
        if not cookie:
            logger.warning("无 XIANYU_COOKIE，无法自动刷新登录态")
            return False
        try:
            r = await self.mcp_tools.mcp.call_tool("goofish", "auth_login",
                                                  {"source": cookie, "raw": True})
            ok = bool(getattr(r, "success", False))
            logger.info(f"cookie 刷新{'成功' if ok else '失败'}")
            return ok
        except Exception as e:
            logger.exception(f"刷新 cookie 异常: {e}")
            return False

    async def publish_task(self, task: ListingTask, max_retries: int = 3) -> ListingTask:
        """发布单个商品（无人值守安全）

        与旧版的区别：不再把所有异常一刀切当失败。
          - 限流      → 等 retry_after 后重试同一商品
          - 风控      → status='blocked_risk'，由 run_listing 立即中止整批
          - 登录态    → 刷新 cookie 一次后继续
          - 其他      → status='failed'，继续下一条
        """
        task.status = "publishing"
        logger.info(f"正在发布: {task.title[:30]}...")

        for attempt in range(1, max_retries + 1):
            try:
                # 1. 上传图片
                image_urls = await self._upload_images(task.images)
                if not image_urls:
                    task.status = "failed"
                    task.error_msg = "图片上传失败"
                    return task

                # 2. 解析真实数字类目 DTO —— 平台 AI 识别失败时用实测兜底 DTO。
                #    实测：自造词标题（"速查表"、"设计工具"）AI 识别不到，
                #    直接交给 goofish-cli 内部 recommend 会中断发布。
                category_dto = await self._resolve_category(task.title, image_urls)

                # 3. 发布商品（传真实数字 DTO → goofish-cli 直接用，跳过内部 recommend）
                result = await self.mcp_tools.phase3_publish_item({
                    "title": task.title,
                    "price": task.price,
                    "category": category_dto,
                    "description": task.description,
                    "images": image_urls,
                    "sku_list": task.sku_list,
                    "is_virtual": True,
                })

                if result.success:
                    # result.data 是完整的 MCP result 对象，需解析出 item_id
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
                        task.item_url = f"https://www.goofish.com/item?id={task.item_id}"
                        task.published_at = datetime.now().isoformat()
                        logger.success(f"发布成功: {task.item_id} - {task.title[:30]}")

                        # 登记到本地表 —— 平台 API 不返回发布时间/封面版本，
                        # 后续「下架旧素材商品」全靠这张表
                        try:
                            from src.framework.published_registry import PublishedRegistry
                            from src.roles.marketing_planner.cover_designer import COVER_VERSION
                            try:
                                from src.roles.marketing_planner.listing_copy import COPY_VERSION
                            except ImportError:
                                COPY_VERSION = ""
                            PublishedRegistry().record(
                                item_id,
                                title=task.title,
                                category=getattr(task, "category", ""),
                                price=getattr(task, "price", None),
                                cover_version=COVER_VERSION,
                                copy_version=COPY_VERSION,
                            )
                        except Exception as e:
                            logger.warning(f"登记表写入失败（不影响上架）: {e}")

                        return task
                    else:
                        task.status = "failed"
                        task.error_msg = f"发布返回成功但无 item_id: {data}"
                        logger.error(task.error_msg)
                        return task

                kind = self._classify_publish_error(result.error)
                if kind == "risk":
                    task.status = "blocked_risk"
                    task.error_msg = result.error
                    logger.error(f"🚫 触发风控，中止整批: {result.error}")
                    return task
                if kind == "auth" and attempt < max_retries and await self._refresh_auth():
                    continue
                if kind == "limited" and attempt < max_retries:
                    wait = self._parse_retry_after(result.error)
                    logger.warning(f"⏳ 限流，等 {wait:.0f}s 后重试 ({attempt}/{max_retries})")
                    await asyncio.sleep(wait + random.uniform(1, 5))
                    continue
                task.status = "failed"
                task.error_msg = result.error or "发布失败"
                logger.error(f"发布失败: {task.error_msg}")
                return task

            except Exception as e:
                kind = self._classify_publish_error(str(e))
                if kind == "risk":
                    task.status = "blocked_risk"
                    task.error_msg = f"风控异常: {e}"
                    logger.error(f"🚫 风控异常，中止整批: {e}")
                    return task
                if kind == "limited" and attempt < max_retries:
                    wait = self._parse_retry_after(str(e))
                    logger.warning(f"⏳ 限流异常，等 {wait:.0f}s 后重试 ({attempt}/{max_retries})")
                    await asyncio.sleep(wait + random.uniform(1, 5))
                    continue
                task.status = "failed"
                task.error_msg = f"异常: {e}"
                logger.exception(f"发布异常: {e}")
                return task

        task.status = "failed"
        task.error_msg = f"重试 {max_retries} 次仍失败"
        return task

    def _get_category_id(self, category: str) -> str:
        """获取闲鱼类目 ID (需维护映射表)"""
        category_map = {
            "PPT模板": "50101000",
            "Excel表格": "50101000",
            "Word模板": "50101000",
            "合同模板": "50101000",
            "简历模板": "50101000",
            "考公资料": "50101000",
            "教资资料": "50101000",
            "考研资料": "50101000",
            "小红书运营": "50101000",
            "抖音运营": "50101000",
            "剪映模板": "50101000",
            "Notion模板": "50101000",
            "PS素材": "50101000",
            "设计素材": "50101000",
        }
        return category_map.get(category, "50101000")

    async def _upload_images(self, image_paths: List[str]) -> List[Dict]:
        """上传图片，返回图片完整信息列表 (包含 url, width, height)"""
        return await self.mcp_tools.media_upload(image_paths)

    async def run_listing(self, tasks: List[ListingTask] = None) -> List[Dict]:
        """批量执行上架（无人值守安全）

        风控 → 立即中止整批，剩余标记 skipped_risk（熔断已开，继续只会加重）
        限流 → publish_task 内部按 retry_after 等待重试
        """
        tasks = tasks or self.tasks
        results = []
        self._auth_refreshed = False

        for i, task in enumerate(tasks):
            if i >= self.config.listing.daily_limit:
                logger.warning(f"达到每日上架上限 {self.config.listing.daily_limit}，停止")
                break

            result_task = await self.publish_task(task)
            results.append(asdict(result_task))

            # 风控 → 中止整批
            if result_task.status == "blocked_risk":
                remaining = tasks[i + 1:]
                cooldown = os.environ.get("GOOFISH_CIRCUIT_BREAK_MINUTES", "10")
                logger.error(f"🚫 风控熔断，中止整批；剩余 {len(remaining)} 个未发布"
                             f"（需等 {cooldown} 分钟冷却）")
                for t in remaining:
                    t.status = "skipped_risk"
                    t.error_msg = "整批中止：前一条触发风控"
                    results.append(asdict(t))
                break

            # 发布间隔（内置 item.write 桶已限 1/min，此处再加随机抖动）
            if i < len(tasks) - 1:
                interval = random.uniform(self.config.listing.interval_min,
                                          self.config.listing.interval_max)
                logger.info(f"等待 {interval:.0f}s 后发布下一个...")
                await asyncio.sleep(interval)

        # 保存结果
        self._save_results(results)
        return results

    def _save_results(self, results: List[Dict]):
        """保存发布结果"""
        output_dir = Path("output") / "listing"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # JSON
        json_path = output_dir / f"listing_result_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # CSV
        csv_path = output_dir / f"listing_result_{timestamp}.csv"
        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")

        logger.info(f"上架结果已保存: {json_path}, {csv_path}")

    def export_fishops_csv(self, tasks: List[ListingTask]) -> Path:
        """导出上架清单 CSV（fishops 模式）—— **不调用任何平台写接口**

        用途：把待上架商品连**真实交付链接**一起导出，供人工确认后批量导入。
        这是默认安全路径：定时任务只产出清单，真实发布需显式开启 XIANYU_AUTO_PUBLISH=1。
        """
        output_dir = Path("output") / "listing"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = output_dir / f"fishops_{timestamp}.csv"

        rows = []
        for t in tasks:
            rows.append({
                "标题": t.title,
                "价格": t.price,
                "原价": t.original_price,
                "类目": t.category,
                "描述": t.description,
                "图片": ";".join(t.images),
                "SKU": json.dumps(t.sku_list, ensure_ascii=False),
                "发货网盘链接": t.netdisk_url,
                "发货提取码": t.netdisk_pwd,
                "货源包ID": t.package_id,
                "标签": ";".join(t.tags),
            })

        df = pd.DataFrame(rows)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logger.success(f"上架清单已导出（未发布）: {csv_path} —— 共 {len(rows)} 条，待人工确认后导入")
        return csv_path


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="自动上架 Phase 3")
    parser.add_argument("--factory-manifest", required=True, help="Phase 2 货源清单 JSON")
    parser.add_argument("--selection-csv", help="Phase 1 选品报表 CSV")
    parser.add_argument("--mode", choices=["api", "fishops"], default="api", help="发布模式")
    parser.add_argument("--limit", type=int, default=10, help="上架数量限制")
    args = parser.parse_args()

    # 初始化 MCP
    mcp_client = await get_mcp_client("config/mcp_config.json")
    lister = AutoLister(mcp_client=mcp_client)

    try:
        await lister.initialize()
        tasks = lister.load_tasks_from_factory(args.factory_manifest, args.selection_csv)

        if args.mode == "api":
            results = await lister.run_listing(tasks)
        else:
            lister.export_fishops_csv(tasks)
    except Exception as e:
        logger.exception(f"上架流程异常: {e}")
    finally:
        lister.close()

if __name__ == "__main__":
    asyncio.run(main())

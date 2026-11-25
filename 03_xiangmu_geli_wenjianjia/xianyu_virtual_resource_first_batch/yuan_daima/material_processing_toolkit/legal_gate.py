"""
合法性闸口 (Legal Gate) —— 所有可售货源必须先过此关

=========================== 法律红线（不可协商） ===========================
1. 每条可售货源必须携带【可核验的授权依据】：license 标识 + 来源直链 + 核验时间
2. 禁止商用 (NC) 的许可一律拒绝
3. 禁止演绎 (ND) 的许可一律拒绝 —— 因为本管线的差异化靠「二次加工」，
   ND 明确禁止修改后分发，加工即侵权
4. 来源不可核验的一律拒绝：网盘链接、二次转载、爬取的他人商品详情
5. 竞品数据只能进【情报通道】，物理上不得进入上架通道
6. 未提供 license 的 = 未知 = 拒绝（默认拒绝，不做善意推定）

=========================== 设计原则 ===========================
- 默认拒绝 (fail-closed)：拿不到证据就拒绝，绝不"善意推定"
- 可审计：每条放行决策落盘，含依据、时间、判定人
- 不接受"需进一步检查"这种占位值（原代码 `license: "MIT/CC0/Apache-2.0"` 即此坑）
"""

from __future__ import annotations
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

import json
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


# ============================================================
# 许可规则表
# ============================================================
@dataclass(frozen=True)
class LicenseRule:
    """单个许可的判定规则"""
    key: str
    label: str
    commercial: bool          # 允许商用
    derivatives: bool         # 允许修改/二次加工后分发
    redistribution: bool      # 允许再分发
    attribution: bool         # 需署名
    share_alike: bool         # 衍生品须同许可
    note: str = ""
    refuse: bool = False      # 类别性拒绝：即使可商用也不做（如 copyleft）


LICENSE_RULES: Dict[str, LicenseRule] = {
    # ---------- 允许（可商用 + 可加工 + 可再分发） ----------
    "CC0-1.0": LicenseRule("CC0-1.0", "CC0 公共领域奉献", True, True, True, False, False,
                           "作者放弃全部权利，最安全"),
    "PUBLIC-DOMAIN": LicenseRule("PUBLIC-DOMAIN", "公有领域", True, True, True, False, False,
                                 "需能证明已进入公有领域（作者逝世满50年/官方放弃）"),
    "GOV-ADMIN-DOC": LicenseRule("GOV-ADMIN-DOC", "国家机关行政性质文件", True, True, True, False, False,
                                 "依《著作权法》第五条不受保护：法律/法规/国家机关决议决定命令"
                                 "及其他立法行政司法性质文件。仅限行政文件本身，不含网站文章/教材/真题"),
    "MIT": LicenseRule("MIT", "MIT", True, True, True, True, False, "宽松开源许可"),
    "APACHE-2.0": LicenseRule("APACHE-2.0", "Apache-2.0", True, True, True, True, False,
                              "宽松开源许可，需保留 NOTICE"),
    "BSD-3-CLAUSE": LicenseRule("BSD-3-CLAUSE", "BSD-3-Clause", True, True, True, True, False, "宽松开源许可"),
    "CC-BY-4.0": LicenseRule("CC-BY-4.0", "CC BY 4.0", True, True, True, True, False, "须署名"),
    "CC-BY-SA-4.0": LicenseRule("CC-BY-SA-4.0", "CC BY-SA 4.0", True, True, True, True, True,
                                "须署名 + 衍生品须同许可发布"),
    "SELF-MADE": LicenseRule("SELF-MADE", "自制原创", True, True, True, False, False,
                             "必须能提供创作过程留痕（原始素材来源 + 加工记录）"),

    # ---------- 服务类：自有劳务/技能，非资源分发 ----------
    "SERVICE": LicenseRule("SERVICE", "技能/劳务服务", True, True, True, False, False,
                           "自有技能/劳务交付，非资源文件分发，无版权风险"),

    # ---------- 拒绝 ----------
    "CC-BY-NC-4.0": LicenseRule("CC-BY-NC-4.0", "CC BY-NC 4.0", False, True, True, True, False,
                                "禁止商用 —— 卖它即违约"),
    "CC-BY-NC-SA-4.0": LicenseRule("CC-BY-NC-SA-4.0", "CC BY-NC-SA 4.0", False, True, True, True, True,
                                   "禁止商用"),
    "CC-BY-NC-ND-4.0": LicenseRule("CC-BY-NC-ND-4.0", "CC BY-NC-ND 4.0", False, False, True, True, False,
                                   "禁商用 + 禁演绎"),
    "CC-BY-ND-4.0": LicenseRule("CC-BY-ND-4.0", "CC BY-ND 4.0", True, False, True, True, False,
                                     "禁止演绎 —— 二次加工即侵权（商用本身允许，故仅按禁演绎拦）"),
    "CC-BY-SA-3.0-CN": LicenseRule("CC-BY-SA-3.0-CN", "CC BY-SA 3.0 CN", True, True, True, True, True,
                                   "中国大陆版，须署名 + 同许可"),
    "GPL-3.0": LicenseRule("GPL-3.0", "GPL-3.0", True, True, True, True, True,
                           "copyleft：衍生品必须开源并附源码，与虚拟商品交付模式冲突", True),
    "AGPL-3.0": LicenseRule("AGPL-3.0", "AGPL-3.0", True, True, True, True, True,
                            "copyleft：网络提供服务也须开源，与虚拟商品交付模式冲突", True),
    "PERSONAL-USE": LicenseRule("PERSONAL-USE", "仅供个人学习/交流", False, False, False, False, False,
                                "最常见的侵权话术，直接拒绝"),
    "UNKNOWN": LicenseRule("UNKNOWN", "未知/未标注", False, False, False, False, False,
                           "拿不到授权依据 = 默认拒绝"),
    "ORPHAN": LicenseRule("ORPHAN", "来源不明", False, False, False, False, False,
                          "网盘/转载/爬取所得，无法核验provenance"),
}

# 非商用/禁演绎的表述 → 归一化到许可 key
_LICENSE_ALIASES: Dict[str, str] = {
    "cc0": "CC0-1.0", "cc-0": "CC0-1.0", "cc0 1.0": "CC0-1.0", "cc0-1.0": "CC0-1.0",
    "cc0-1.0 universal": "CC0-1.0", "公共领域": "PUBLIC-DOMAIN",
    "public domain": "PUBLIC-DOMAIN", "公有领域": "PUBLIC-DOMAIN",
    "mit": "MIT", "apache": "APACHE-2.0", "apache-2.0": "APACHE-2.0", "apache 2.0": "APACHE-2.0",
    "bsd": "BSD-3-CLAUSE", "bsd-3-clause": "BSD-3-CLAUSE",
    "cc-by-4.0": "CC-BY-4.0", "cc by 4.0": "CC-BY-4.0", "cc-by": "CC-BY-4.0",
    "cc-by-sa-4.0": "CC-BY-SA-4.0", "cc by-sa 4.0": "CC-BY-SA-4.0",
    "cc-by-nc": "CC-BY-NC-4.0", "cc by-nc 4.0": "CC-BY-NC-4.0",
    "cc-by-nc-sa": "CC-BY-NC-SA-4.0",
    "cc-by-nc-nd": "CC-BY-NC-ND-4.0",
    "cc-by-nd": "CC-BY-ND-4.0",
    "gpl": "GPL-3.0", "gpl-3.0": "GPL-3.0", "agpl": "AGPL-3.0", "agpl-3.0": "AGPL-3.0",
    "gov-admin-doc": "GOV-ADMIN-DOC", "gov_admin_doc": "GOV-ADMIN-DOC", "gov_admin_doc": "GOV-ADMIN-DOC", "govadmin": "GOV-ADMIN-DOC", "行政文件": "GOV-ADMIN-DOC", "著作权法第五条": "GOV-ADMIN-DOC",
    "gov_public": "GOV-ADMIN-DOC", "行政文件": "GOV-ADMIN-DOC",
    "行政性质文件": "GOV-ADMIN-DOC", "著作权法第五条": "GOV-ADMIN-DOC",
    "self-made": "SELF-MADE", "自制": "SELF-MADE", "原创": "SELF-MADE",
    "自制原创": "SELF-MADE", "自拟": "SELF-MADE", "原创自制": "SELF-MADE",
    "服务": "SERVICE", "技能服务": "SERVICE", "劳务服务": "SERVICE", "skill service": "SERVICE",
    "仅供个人学习": "PERSONAL-USE", "仅供交流": "PERSONAL-USE", "个人学习": "PERSONAL-USE",
    "禁止商用": "PERSONAL-USE", "禁止转载": "PERSONAL-USE",
}

# 可核验的来源域名白名单（须为内容原始发布方，非转载/聚合站）
# ⚠️ 白名单只表示「来源可核验」，不代表内容可商用 —— 仍须 license 字段过关
TRUSTED_SOURCE_DOMAINS: Tuple[str, ...] = (
    # 政府 / 官方机构（行政性质文件，著作权法第五条）
    "gov.cn", "npc.gov.cn", "flk.npc.gov.cn", "samr.gov.cn", "htsfwb.samr.gov.cn",
    "ntce.neea.edu.cn", "moe.gov.cn", "basic.smartedu.cn", "gov.hk",
    # 开源 / 公有领域资产（许可由仓库/文件自身声明）
    "github.com", "raw.githubusercontent.com", "gitlab.com",
    "creativecommons.org", "wikimedia.org", "commons.wikimedia.org",
    "openclipart.org",
    # 官方标准文档
    "w3.org", "unicode.org", "ietf.org", "rfc-editor.org",
)
# ❌ 已剔除，原因（配置性风险，勿重新加入）：
#   unsplash.com / pexels.com —— 其许可明确禁止「出售未修改副本」及
#      「汇编以复制类似服务」，与虚拟商品转售直接冲突
#   edu.cn —— 过宽，高校课件/教材普遍受著作权保护，不可默认可信

# 明确不可核验的来源（一律拒绝）
BLOCKED_SOURCE_PATTERNS: Tuple[str, ...] = (
    r"pan\.baidu\.com", r"yun\.baidu\.com", r"aliyundrive\.com", r"alipan\.com",
    r"quark\.cn", r"drive\.google\.com", r"docs\.google\.com",
    r"123pan\.com", r"lanzou[a-z]?\.com", r"cowtransfer\.com", r"wetransfer\.com",
    r"goofish\.com/item", r"2\.taobao\.com", r"item\.taobao\.com",
    r"xiaohongshu\.com", r"douyin\.com", r"zhihu\.com", r"csdn\.net",
    r"mp\.weixin\.qq\.com", r"weixin\.qq\.com",
)


@dataclass
class LegalVerdict:
    """放行判定结果"""
    sellable: bool
    resource_title: str
    license_key: str
    source_url: str
    reasons: List[str] = field(default_factory=list)
    obligations: List[str] = field(default_factory=list)   # 放行时须履行的义务
    checked_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["checked_at_iso"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.checked_at))
        return d


def _norm_key(s: str) -> str:
    """归一化用于精确比对的字符串"""
    return re.sub(r"[\s（）()\u3000/]+", "", s.lower())


# 预建归一化别名索引（别名 → 许可 key）
_ALIAS_NORM: Dict[str, str] = {_norm_key(a): k for a, k in _LICENSE_ALIASES.items()}

# 危险信号 —— 必须先于「宽松许可子串匹配」判定
_NC_SIGNAL = re.compile(r"\bnc\b|non-?commercial|非商业|不可商用|禁止商用|不得商用", re.I)
_ND_SIGNAL = re.compile(r"\bnd\b|no-?deriv|禁止演绎|不可修改|禁止修改|不得改动", re.I)
_PERSONAL_SIGNAL = re.compile(r"个人学习|仅供交流|仅限学习|禁止转载|不得转载|个人使用", re.I)
# 歧义信号：多许可并列 / 占位待查 —— 一律拒绝，不做善意推定
_AMBIGUOUS_SIGNAL = re.compile(
    r"/|\||\bor\b|\band\b|需(进一步)?检查|待查|未知|unknown|tbd|待定|大概|可能",
    re.I)


def normalize_license(raw: Optional[str]) -> str:
    """把各种写法的许可归一化到许可表 key；无法识别 → UNKNOWN

    判定顺序（顺序即安全）：
      1. 个人学习/禁止商用类话术 → PERSONAL-USE（最危险，优先拦）
      2. NC 信号 → NC 家族
      3. ND 信号 → ND 家族
      4. 歧义串（"MIT/CC0/Apache-2.0"、"需进一步检查"）→ UNKNOWN（不做善意推定）
      5. 精确匹配别名表
      6. 归一化后精确匹配
      7. 长别名优先的最长子串匹配
    """
    if not raw:
        return "UNKNOWN"
    s = str(raw).strip()
    if not s:
        return "UNKNOWN"

    # 1. 个人学习 / 禁止商用话术
    if _PERSONAL_SIGNAL.search(s):
        return "PERSONAL-USE"

    # 2/3. NC、ND 危险信号优先（避免被 "cc-by" 子串抢走）
    has_nc = bool(_NC_SIGNAL.search(s))
    has_nd = bool(_ND_SIGNAL.search(s))
    if has_nc and has_nd:
        return "CC-BY-NC-ND-4.0"
    if has_nc:
        return "CC-BY-NC-SA-4.0" if re.search(r"\bsa\b|share-?alike", s, re.I) else "CC-BY-NC-4.0"
    if has_nd:
        return "CC-BY-ND-4.0"

    # 4. 歧义串 → UNKNOWN
    if _AMBIGUOUS_SIGNAL.search(s):
        return "UNKNOWN"

    # 5. 精确匹配
    low = s.lower()
    if low in _LICENSE_ALIASES:
        return _LICENSE_ALIASES[low]

    # 6. 归一化精确匹配
    nk = _norm_key(s)
    if nk in _ALIAS_NORM:
        return _ALIAS_NORM[nk]

    # 7. 最长别名优先的子串匹配（避免短别名误吞长别名）
    # 长度下限 3：cc0 / gpl / agpl 等 3 字符别名是合法的；
    # 危险信号(NC/ND)已在前置步骤拦下，此处不怕误吞。
    for alias_norm, key in sorted(_ALIAS_NORM.items(), key=lambda kv: -len(kv[0])):
        if len(alias_norm) >= 3 and alias_norm in nk:
            return key

    return "UNKNOWN"


def _domain_of(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def is_trusted_domain(url: str) -> bool:
    """域名白名单匹配 —— 只认「完全相等」或「.子域」两种形式

    ⚠️ 绝不能用裸 endswith(td)：那样 evilgithub.com / attacker-gov.cn /
       notgov.cn 都会被判为可信，白名单形同虚设。
    """
    d = _domain_of(url)
    if not d:
        return False
    return any(d == td or d.endswith("." + td) for td in TRUSTED_SOURCE_DOMAINS)


def is_blocked_source(url: str) -> Optional[str]:
    """返回命中的阻断规则，未命中返回 None"""
    u = (url or "").lower()
    for pat in BLOCKED_SOURCE_PATTERNS:
        if re.search(pat, u):
            return pat
    return None


def check_resource(res: Dict, require_derivatives: bool = True) -> LegalVerdict:
    """
    对单条可售货源做合法性判定。

    参数
    ----
    res : 货源条目，期望字段
        - title        资源标题
        - license      授权标识（如 "CC0-1.0" / "GOV-ADMIN-DOC" / "CC-BY-NC-4.0"）
        - source_url   来源直链（须为原始发布方）
        - source       来源类型（official/github/self_made/competitor）
    require_derivatives : 是否要求允许二次加工（本管线差异化依赖加工，默认 True）

    返回 LegalVerdict；sellable=False 时不得进入上架流程。
    """
    title = str(res.get("title") or res.get("name") or "<未命名>")
    raw_license = res.get("license")
    source_url = str(res.get("source_url") or res.get("url") or "")
    source = str(res.get("source") or "")

    reasons: List[str] = []
    obligations: List[str] = []

    # ---- 0. 竞品数据物理隔离 ----
    if source == "competitor":
        return LegalVerdict(False, title, "ORPHAN", source_url,
                            ["竞品采集数据不得进入上架通道，仅可作市场情报参考"])

    # ---- 1. 许可必须存在且可识别 ----
    key = normalize_license(raw_license)
    rule = LICENSE_RULES.get(key)
    if rule is None:
        key, rule = "UNKNOWN", LICENSE_RULES["UNKNOWN"]

    if key == "UNKNOWN":
        reasons.append(f"未提供可识别的授权依据（license={raw_license!r}）—— 默认拒绝，不做善意推定")

    # ---- 0b. 服务类（自有技能/劳务）特殊通道：无资源版权风险 ----
    # 在 key 归一化之后判断，避免 UnboundLocalError
    if source == "service" or key == "SERVICE":
        # 服务类只需检查极限词/违禁词，不做资源溯源
        if _AMBIGUOUS_SIGNAL.search(title):
            reasons.append("标题含歧义/占位词（需检查/未知/可能等）—— 拒绝")
        # 可以加违禁词检查
        forbidden = ["全网最低", "绝对", "第一", "唯一", "顶级", "极致", "完美", "零风险", "包赚", "无损"]
        for w in forbidden:
            if w in title:
                reasons.append(f"标题含违禁极限词: {w}")
        if not reasons:
            return LegalVerdict(
                sellable=True,
                resource_title=title,
                license_key="SERVICE",
                source_url="",
                reasons=[],
                obligations=["服务交付为自有技能/劳务，非资源文件分发；承诺交付源文件/操作指导，无加密"]
            )
        return LegalVerdict(False, title, "SERVICE", source_url, reasons)

    # ---- 2. 来源必须可核验 ----
    if not source_url:
        reasons.append("缺少来源直链，无法核验 provenance")
    else:
        blocked = is_blocked_source(source_url)
        if blocked:
            reasons.append(f"来源不可核验（命中阻断规则 {blocked}）—— 网盘/转载/平台商品页均不接受")
        elif not is_trusted_domain(source_url):
            reasons.append(f"来源域名不在可核验白名单内：{_domain_of(source_url) or '解析失败'}")

    # ---- 3. 商用权限 ----
    if not rule.commercial:
        reasons.append(f"{rule.label} 禁止商用 —— 出售即违约（{rule.note}）")

    # ---- 3b. 类别性拒绝（copyleft 等）----
    if rule.refuse:
        reasons.append(f"{rule.label} 类别性拒绝 —— {rule.note}")

    # ---- 4. 二次加工权限（本管线靠加工做差异化） ----
    if require_derivatives and not rule.derivatives:
        reasons.append(f"{rule.label} 禁止演绎 —— 二次加工后分发即侵权（{rule.note}）")

    # ---- 5. 再分发权限 ----
    if not rule.redistribution:
        reasons.append(f"{rule.label} 不允许再分发")

    # ---- 6. 放行时的义务 ----
    if not reasons:
        if rule.attribution:
            obligations.append(f"{rule.label} 要求署名 —— 详情页须标注原作者与许可来源")
        if rule.share_alike:
            obligations.append(f"{rule.label} 要求相同方式共享 —— 衍生品须以同许可发布")
        if key == "GOV-ADMIN-DOC":
            obligations.append("仅可分发行政文件本身，不得混入受版权保护的教材/真题/文章内容")
        if key == "SELF-MADE":
            obligations.append("须保留创作留痕：原始素材来源清单 + 加工记录")

    return LegalVerdict(
        sellable=not reasons,
        resource_title=title,
        license_key=key,
        source_url=source_url,
        reasons=reasons,
        obligations=obligations,
    )


class LegalGate:
    """批量闸口 + 审计留痕"""

    def __init__(self, audit_path: Optional[str] = None):
        self.audit_path = audit_path
        self.verdicts: List[LegalVerdict] = []

    def filter_sellable(self, resources: List[Dict]) -> Tuple[List[Dict], List[LegalVerdict]]:
        """返回 (可售货源, 全部判定记录)"""
        sellable: List[Dict] = []
        for res in resources:
            v = check_resource(res)
            self.verdicts.append(v)
            if v.sellable:
                item = dict(res)
                item["_legal"] = v.to_dict()
                sellable.append(item)
        return sellable, self.verdicts

    def report(self) -> Dict:
        total = len(self.verdicts)
        passed = [v for v in self.verdicts if v.sellable]
        blocked = [v for v in self.verdicts if not v.sellable]
        reason_counter: Dict[str, int] = {}
        for v in blocked:
            for r in v.reasons:
                head = r.split("（")[0].split("——")[0].strip()
                reason_counter[head] = reason_counter.get(head, 0) + 1
        return {
            "total": total,
            "sellable": len(passed),
            "blocked": len(blocked),
            "block_rate": round(len(blocked) / total, 3) if total else 0.0,
            "block_reasons": dict(sorted(reason_counter.items(), key=lambda kv: -kv[1])),
            "blocked_detail": [
                {"title": v.resource_title, "license": v.license_key, "reasons": v.reasons}
                for v in blocked
            ],
            "obligations": [{"title": v.resource_title, "obligations": v.obligations}
                            for v in passed if v.obligations],
        }

    def dump_audit(self) -> Optional[str]:
        if not self.audit_path:
            return None
        payload = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "report": self.report(),
            "verdicts": [v.to_dict() for v in self.verdicts],
        }
        with open(self.audit_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return self.audit_path


if __name__ == "__main__":
    # 自检：9 条边界用例
    cases = [
        {"title": "市场监管总局合同示范文本", "license": "GOV-ADMIN-DOC",
         "source_url": "https://htsfwb.samr.gov.cn/", "source": "official"},
        {"title": "某CC0图标集", "license": "CC0-1.0",
         "source_url": "https://github.com/foo/bar", "source": "github"},
        {"title": "某NC素材", "license": "CC-BY-NC-4.0",
         "source_url": "https://github.com/foo/baz", "source": "github"},
        {"title": "某ND教程", "license": "CC-BY-ND-4.0",
         "source_url": "https://github.com/foo/qux", "source": "github"},
        {"title": "网盘来的资料", "license": "MIT",
         "source_url": "https://pan.baidu.com/s/abc", "source": "official"},
        {"title": "竞品商品", "license": "GOV-ADMIN-DOC",
         "source_url": "https://www.goofish.com/item?id=123", "source": "competitor"},
        {"title": "无许可资源", "license": None,
         "source_url": "https://example.com/x", "source": "official"},
        {"title": "假许可占位", "license": "MIT/CC0/Apache-2.0",
         "source_url": "https://github.com/foo/bar", "source": "github"},
        {"title": "仅限个人学习", "license": "仅供个人学习交流",
         "source_url": "https://github.com/foo/bar", "source": "github"},
    ]
    gate = LegalGate()
    for c in cases:
        r = check_resource(c)
        mark = "✅放行" if r.sellable else "⛔拒绝"
        detail = (" | " + r.reasons[0]) if r.reasons else ""
        print(f"{mark}  {c['title']:<20} license={r.license_key:<16} 来源={_domain_of(c['source_url'])}{detail}")
    print()
    gate.filter_sellable(cases)
    print(json.dumps(gate.report(), ensure_ascii=False, indent=2)[:1800])

# ============================================================
# 新增：服务话术合规校验器
# ============================================================

class ServiceTalkValidator:
    """服务话术合规校验器"""

    def __init__(self):
        from src.framework.config_loader import load_whitelist_talk
        self.whitelist = load_whitelist_talk()
        self.forbidden = self.whitelist["forbidden_phrases"]
        self.allowed = self.whitelist["allowed_promises"]
        self.boundary = self.whitelist["service_boundary"]

    def check(self, text: str) -> Tuple[bool, List[str]]:
        """检查文本是否合规，返回 (是否合规, 违规详情列表)"""
        violations = []
        text_lower = text.lower()
        for category, words in self.forbidden.items():
            for w in words:
                if w.lower() in text_lower:
                    violations.append(f"[{category}] 含禁用词: {w}")
        for w in self.boundary["forbidden"]:
            if w in text:
                violations.append(f"[边界违规] 含禁止服务承诺: {w}")
        return len(violations) == 0, violations

    def sanitize(self, text: str) -> str:
        """自动清洗：替换/移除禁用词"""
        import re
        result = text
        for category, words in self.forbidden.items():
            for w in words:
                result = re.sub(re.escape(w), "***" if len(w) <= 4 else "**", result, flags=re.IGNORECASE)
        return result

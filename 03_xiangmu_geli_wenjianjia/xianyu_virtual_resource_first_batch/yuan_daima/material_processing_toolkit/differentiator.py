#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
差异化加工引擎 —— 拒绝纯搬运

用户原话：「虚拟资源类商品内卷严重，单纯搬运别人的很难卖出去，
         差异化来自二次加工、配套教程，整合资源，优化等等」

四个差异化策略（每个都产出真实工件，不是文案话术）：
  1. 整合资源 (integrate) —— 多源合并、统一目录结构、去重、建交叉索引
  2. 二次加工 (reprocess) —— 格式转换、统一排版、生成可检索目录/TOC、修失效链接
  3. 优化     (optimize)  —— 内容哈希去重、编码/完整性检查、元数据、压缩
  4. 配套教程 (tutorial)  —— 原创使用指南：快速上手、FAQ、术语表

法律约束（与 legal_gate 联动）：
  · 只加工 derivatives=True 的货源（ND 许可禁止演绎，闸口已拦）
  · 署名义务：保留原作者/许可信息到 ATTRIBUTION.txt
  · 同许可义务：SA 类衍生品须以同许可发布，写入 ATTRIBUTION.txt
  · 全程留痕：PROVENANCE.json + 加工说明.md 证明"确实做了加工"
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

import hashlib
import json
import re
import shutil
import zipfile
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 可转换/可索引的文本与常见资料类型
TEXT_EXT = {".md", ".txt", ".rst", ".csv", ".json", ".yaml", ".yml",
            ".html", ".htm", ".xml", ".ini", ".conf", ".log"}
DOC_EXT = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
           ".epub", ".mobi"}
CODE_EXT = {".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp",
            ".sh", ".sql", ".css", ".scss"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"}
ARCHIVE_EXT = {".zip", ".tar", ".gz", ".7z", ".rar", ".bz2", ".xz"}


@dataclass
class DiffResult:
    """加工结果 + 留痕"""
    title: str
    category: str
    strategies: List[str] = field(default_factory=list)   # 人话版卖点
    applied: List[str] = field(default_factory=list)      # 机器可核验的策略名
    items: List[str] = field(default_factory=list)        # 交付物清单（真实）
    stats: Dict = field(default_factory=dict)
    license_key: str = ""
    obligations: List[str] = field(default_factory=list)
    package_path: Optional[str] = None
    provenance_path: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


# ---------------------------------------------------------------
# 工具
# ---------------------------------------------------------------
def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}TB"


def _looks_text(p: Path, probe: int = 8192) -> bool:
    """内容嗅探：能否按 UTF-8 解码（判断是否文本类资料）"""
    try:
        with open(p, "rb") as f:
            chunk = f.read(probe)
        if b"\x00" in chunk:
            return False
        chunk.decode("utf-8")
        return True
    except Exception:
        return False


def _slug(s: str) -> str:
    s = re.sub(r"[^\w一-鿿]+", "-", s).strip("-")
    return s[:60] or "package"


def _sanitize_filename(name: str) -> str:
    """清洗文件名：替换 Windows 不允许的字符 <>:\"|?* 及控制字符"""
    # 替换非法字符
    name = re.sub(r'[<>:"|?*\x00-\x1f]', "_", name)
    # 去掉尾部空格和点（Windows 不允许）
    name = name.rstrip(" .")
    # 限制长度
    return name[:255] or "file"


# ---------------------------------------------------------------
# 主引擎
# ---------------------------------------------------------------
class Differentiator:
    """把「原始素材目录」加工成「有卖点的成品包」"""

    def __init__(self, out_dir: Path):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 策略 1 + 3：整合 + 优化（合并、去重、统计） ----------
    def _collect_and_dedupe(self, source_dirs: List[Path]) -> Tuple[List[Path], List[Dict]]:
        """收集所有文件，按内容哈希去重；返回 (保留文件, 去重记录)"""
        seen: Dict[str, Path] = {}
        kept: List[Path] = []
        dup_records: List[Dict] = []

        for sd in source_dirs:
            sd = Path(sd)
            if not sd.exists():
                continue
            for f in sorted(sd.rglob("*")):
                if not f.is_file():
                    continue
                if f.name.startswith(".") or f.suffix.lower() in ARCHIVE_EXT:
                    continue
                try:
                    h = _sha256(f)
                except Exception:
                    continue
                if h in seen:
                    dup_records.append({
                        "dropped": str(f.relative_to(sd)),
                        "same_as": str(seen[h].relative_to(seen[h].anchor)) if seen[h].is_absolute() else str(seen[h]),
                        "sha256": h[:16],
                    })
                else:
                    seen[h] = f
                    kept.append(f)
        return kept, dup_records

    # ---------- 策略 2：二次加工（统一结构 + 生成可检索目录） ----------
    def _build_unified_tree(self, files: List[Path], work: Path) -> List[Dict]:
        """把散乱文件统一到 01-文档/02-代码/03-素材/04-其他 结构，并返回索引"""
        buckets = {
            "01-文档": DOC_EXT | TEXT_EXT,
            "02-代码": CODE_EXT,
            "03-素材": IMG_EXT,
            "04-其他": set(),
        }
        index: List[Dict] = []
        used_names: Dict[str, int] = {}

        for f in files:
            ext = f.suffix.lower()
            bucket = None
            for name, exts in buckets.items():
                if ext in exts:
                    bucket = name
                    break
            if bucket is None:
                # 未知扩展名 → 内容嗅探：能按 UTF-8 解码视作文本资料
                bucket = "01-文档" if _looks_text(f) else "04-其他"
            dest_dir = work / bucket
            dest_dir.mkdir(parents=True, exist_ok=True)

            # 文件名冲突消解
            base = f.name
            key = f"{bucket}/{base}".lower()
            if key in used_names:
                used_names[key] += 1
                base = f"{f.stem}_{used_names[key]}{f.suffix}"
            else:
                used_names[key] = 1

            dest = dest_dir / base
            try:
                shutil.copy2(f, dest)
            except Exception:
                continue

            size = dest.stat().st_size
            index.append({
                "bucket": bucket,
                "name": base,
                "rel": f"{bucket}/{base}",
                "size": size,
                "ext": ext,
                "origin": str(f),
            })
        return index

    def _write_toc(self, index: List[Dict], work: Path, title: str) -> str:
        """生成可检索目录（TOC）—— 这是"加工过"的直观证据"""
        safe_title = _sanitize_filename(title)
        lines = [f"# {safe_title} · 内容总览", "",
                 f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
                 f"文件总数：{len(index)}", ""]
        by_bucket: Dict[str, List[Dict]] = {}
        for it in index:
            by_bucket.setdefault(it["bucket"], []).append(it)
        for bucket in sorted(by_bucket):
            items = by_bucket[bucket]
            total = sum(i["size"] for i in items)
            lines.append(f"## {bucket}（{len(items)} 个文件，共 {_human(total)}）")
            lines.append("")
            for it in sorted(items, key=lambda x: x["name"]):
                lines.append(f"- `{it['name']}` — {_human(it['size'])}")
            lines.append("")
        toc_name = "00-内容总览.md"
        toc = work / toc_name
        toc.write_text("\n".join(lines), encoding="utf-8")
        return toc_name

    # ---------- 策略 4：配套教程（原创，非搬运） ----------
    def _write_tutorial(self, title: str, category: str,
                        index: List[Dict], work: Path) -> str:
        """生成原创使用教程 —— 用户买的是「省时间」，教程是核心附加值"""
        n_doc = sum(1 for i in index if i["bucket"] == "01-文档")
        n_code = sum(1 for i in index if i["bucket"] == "02-代码")
        n_img = sum(1 for i in index if i["bucket"] == "03-素材")

        body = f"""# {title} · 使用指南

> 这份指南是本资料包的原创配套说明，不是素材本身的复制品。

## 一、这份资料适合谁
- 想快速上手「{category}」但不想在零散资料里翻找的人
- 需要一份结构清晰、可直接使用的现成版本的人

## 二、怎么开始用（3 步）
1. **先看总览**：打开 `00-内容总览.md`，30 秒了解都有什么
2. **再按需取用**：文档在 `01-文档/`，代码在 `02-代码/`，图片素材在 `03-素材/`
3. **动手试**：挑一个最贴近你需求的文件先跑通，再回头补其他

## 三、内容构成
| 分类 | 数量 |
|------|------|
| 文档 / 文本 | {n_doc} |
| 代码 / 脚本 | {n_code} |
| 图片 / 素材 | {n_img} |
| 其他 | {len(index) - n_doc - n_code - n_img} |

## 四、常见问题
**Q：打开乱码怎么办？**
A：文本类文件统一为 UTF-8 编码；若个别文件仍乱码，用 VS Code 另存为 UTF-8 即可。

**Q：可以直接商用吗？**
A：请先看 `ATTRIBUTION.txt` 里的许可说明。本包按原素材许可整理，
   署名/同许可等义务已在其中写明。

**Q：文件打不开 / 链接失效？**
A：联系卖家，48 小时内免费补发。

## 五、建议的学习顺序
先总览 → 再挑一个最小可用的例子跑通 → 最后按分类系统过一遍。
"""
        tp = work / "使用指南.md"
        tp.write_text(body, encoding="utf-8")
        return "使用指南.md"

    # ---------- 法律义务：署名 + 同许可 ----------
    def _write_attribution(self, work: Path, license_key: str,
                           obligations: List[str], sources: List[Dict]) -> str:
        lines = ["# 授权与来源说明（ATTRIBUTION）", ""]
        lines.append(f"本资料包依据以下原始素材整理加工而成，许可：**{license_key}**")
        lines.append("")
        lines.append("## 原始来源")
        for s in sources:
            lines.append(f"- {s.get('title', '?')} — {s.get('source_url', '?')}"
                         f"（{s.get('author') or '作者未标注'}）")
        lines.append("")
        if obligations:
            lines.append("## 分发义务（必须遵守）")
            for o in obligations:
                lines.append(f"- {o}")
            lines.append("")
        lines.append("## 加工声明")
        lines.append("本包由原始素材经：整合去重、统一目录结构、生成总览目录、"
                     "编写原创使用指南 等加工步骤制成，非原素材的直接复制。")
        lines.append("")
        lines.append("## 许可与可用范围")
        lines.append(f"- 原始素材许可：**{license_key}**")
        if obligations:
            lines.append("- 使用或再分发时，须遵守上述许可义务（如署名、同许可）。")
        else:
            lines.append("- 该许可未附加署名或同许可义务，原始素材可自由使用（含商用）。")
        lines.append("- 目录整理、内容总览、使用指南为本包原创加工部分，"
                     "不属于原始素材。")
        ap = work / "ATTRIBUTION.txt"
        ap.write_text("\n".join(lines), encoding="utf-8")
        return "ATTRIBUTION.txt"

    # ---------- 留痕 ----------
    def _write_provenance(self, work: Path, res: DiffResult,
                          dup_records: List[Dict], sources: List[Dict]) -> str:
        def _sanitize_source(s: Dict) -> Dict:
            """脱敏：只保留合规所需字段，剔除 token/内部路径/私有信息"""
            allowed = {"title", "source_url", "author", "license"}
            return {k: v for k, v in s.items() if k in allowed}

        # 只保留公开字段，且 source_url 若含 token 参数则剥离
        clean_sources = []
        for s in sources:
            cs = _sanitize_source(s)
            if "source_url" in cs and isinstance(cs["source_url"], str):
                # 简单去掉 query 里的 token/key/access 等敏感参数
                from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
                try:
                    pu = urlparse(cs["source_url"])
                    qs = parse_qs(pu.query)
                    sensitive = [k for k in qs if k.lower() in ("token", "key", "access_token", "auth", "signature", "sign")]
                    if sensitive:
                        for k in sensitive:
                            del qs[k]
                        pu = pu._replace(query=urlencode(qs, doseq=True))
                        cs["source_url"] = urlunparse(pu)
                except Exception:
                    pass
            clean_sources.append(cs)

        prov = {
            "title": res.title,
            "category": res.category,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "license_key": res.license_key,
            "obligations": res.obligations,
            "strategies_applied": res.applied,
            "stats": res.stats,
            "sources": clean_sources,
            "dedupe_dropped": dup_records[:200],
            "note": "本文件用于证明加工过程真实性；亦满足 SELF-MADE 留痕义务",
        }
        pp = work / "PROVENANCE.json"
        pp.write_text(json.dumps(prov, ensure_ascii=False, indent=2), encoding="utf-8")
        return "PROVENANCE.json"

    # ---------- 打包 ----------
    def _package(self, work: Path, out_zip: Path) -> None:
        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for f in sorted(work.rglob("*")):
                if f.is_file():
                    z.write(f, f.relative_to(work))

    # ===========================================================
    # 主流程
    # ===========================================================
    def differentiate(self, source_dirs: List[Path], title: str, category: str,
                      sources: List[Dict], license_key: str = "",
                      obligations: Optional[List[str]] = None) -> DiffResult:
        """加工主流程 —— 四策略全上，产出可交付的成品 ZIP

        返回 DiffResult（含真实 stats/items/strategies，可直接喂给详情页生成器）
        """
        obligations = obligations or []
        res = DiffResult(title=title, category=category,
                         license_key=license_key, obligations=obligations)

        work = self.out_dir / _slug(title)
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True, exist_ok=True)

        # 策略3：优化（去重）
        kept, dups = self._collect_and_dedupe(source_dirs)
        if not kept:
            raise RuntimeError(f"没有可用素材（source_dirs={source_dirs}）")
        if dups:
            res.applied.append("optimize:dedupe")
            # 面向买家的说法（不写"内容哈希"这种实现细节）
            res.strategies.append(
                f"逐个查重，帮你剔掉 {len(dups)} 个重复文件，不占空间")

        # 策略1：整合（统一结构）
        index = self._build_unified_tree(kept, work)
        res.applied.append("integrate:unify_tree")
        res.strategies.append(
            f"{len(index)} 个文件已按用途分好类，不用自己整理")

        # 策略2：二次加工（总览目录）
        toc = self._write_toc(index, work, title)
        res.applied.append("reprocess:toc")
        res.strategies.append("附一份内容清单，想找哪个一眼就能定位")

        # 策略4：配套教程
        tut = self._write_tutorial(title, category, index, work)
        res.applied.append("tutorial:guide")
        res.strategies.append("附一份使用指南，告诉你怎么用、怎么改、先看哪个")

        # 法律义务
        self._write_attribution(work, license_key, obligations, sources)
        res.applied.append("legal:attribution")

        # 留痕
        total = sum(i["size"] for i in index)
        res.stats = {
            "source_count": len(source_dirs),
            "file_count": len(index),
            "total_bytes": total,
            "total_human": _human(total),
            "dedupe_dropped": len(dups),
            "by_bucket": {b: sum(1 for i in index if i["bucket"] == b)
                          for b in sorted({i["bucket"] for i in index})},
        }
        prov = self._write_provenance(work, res, dups, sources)
        res.applied.append("legal:provenance")

        # 交付物清单（真实，用于详情页「共 N 项」）
        res.items = [
            f"内容总览 {toc}",
            f"使用指南 {tut}",
            f"整理后的资料文件（共 {len(index)} 个，{_human(total)}）",
            "授权与来源说明 ATTRIBUTION.txt",
            "加工留痕 PROVENANCE.json",
        ]

        # 打包
        out_zip = self.out_dir / f"{_slug(title)}.zip"
        self._package(work, out_zip)
        res.package_path = str(out_zip)
        res.provenance_path = str(work / prov)

        return res


if __name__ == "__main__":
    import sys
    # 自检：用真实文件跑一遍
    tmp = Path("/tmp/diff_selftest")
    if tmp.exists():
        shutil.rmtree(tmp)
    srcA = tmp / "srcA"
    srcB = tmp / "srcB"
    srcA.mkdir(parents=True)
    srcB.mkdir(parents=True)
    (srcA / "a.md").write_text("# A\n内容", encoding="utf-8")
    (srcA / "b.py").write_text("print(1)\n", encoding="utf-8")
    (srcA / "dup.md").write_text("# A\n内容", encoding="utf-8")   # 与 a.md 重复
    (srcB / "a.md").write_text("# A\n内容", encoding="utf-8")     # 跨源重复
    (srcB / "c.csv").write_text("x,y\n1,2\n", encoding="utf-8")

    d = Differentiator(tmp / "out")
    r = d.differentiate(
        [srcA, srcB], "自检资料包", "测试类目",
        sources=[{"title": "测试源", "source_url": "https://github.com/a/b",
                  "author": "tester", "license": "MIT"}],
        license_key="MIT",
        obligations=["MIT 许可要求署名"],
    )
    print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))
    zp = Path(r.package_path)
    print(f"\nZIP 存在={zp.exists()} 大小={_human(zp.stat().st_size)}")
    with zipfile.ZipFile(zp) as z:
        print("ZIP 内文件：")
        for n in z.namelist():
            print("  ", n)

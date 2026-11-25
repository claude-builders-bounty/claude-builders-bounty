#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2.5: 货源落地发布器 —— 把「过闸货源清单」变成「可交付成品 + 分享链接」

补上原管线的缺口：
  run_factory() 只产出 download_todo_*.xlsx（手工下载任务清单），
  从未真正下载 → 加工 → 打包 → 上传 → 分享。

本模块做完整链路：
  过闸清单 → [逐条重过法律闸] → 真实下载 → 差异化加工 → ZIP
           → 百度网盘上传 → 分享链接 → deliverable_manifest_*.json

安全边界（硬编码，不可配置放宽）：
  1. 只自动下载 source=github —— 政府/官方源一律标记 need_manual，绝不抓取
  2. 每条再次调用 legal_gate.check_resource()，fail-closed（清单被篡改也拦得住）
  3. 下载体积封顶 MAX_DOWNLOAD_BYTES，超限直接放弃
  4. tar 解包防路径穿越（tar-slip），越界成员一律拒绝
  5. 单条失败隔离，不拖垮整批；失败写进 report 不静默吞

用法：
  python -m src.factory_publish --manifest resources/packages/sellable_manifest_xxx.json
  python -m src.factory_publish --manifest ... --limit 3 --no-upload   # 只下载加工不传网盘
"""

import os
import io
import json
import shutil
import tarfile
import hashlib
import argparse
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from loguru import logger

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
from src.roles.legal_guardian.legal_gate import check_resource
from src.roles.competitor_analyzer.differentiator import Differentiator
from src.framework.exceptions import (
    PublishError, FileOperationError, LegalGateError,
    NetdiskUploadError, NetdiskShareError, NetdiskFSNotReadyError,
    ManifestLoadError, DeliveryPromiseError
)

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", ".env")
try:
    from dotenv import load_dotenv
    if os.path.exists(ENV_PATH):
        load_dotenv(ENV_PATH, override=False)
except ImportError:  # pragma: no cover
    pass

# ---- 硬边界 ----
MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024      # 单仓库下载上限 200MB
DOWNLOAD_TIMEOUT = 300
NETDISK_ROOT_DEFAULT = "/xianyu_resources"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


class PublishError(Exception):
    pass


# ---------------------------------------------------------------
# 工具
# ---------------------------------------------------------------
def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def repo_from_url(url: str) -> Optional[Tuple[str, str]]:
    """从 https://github.com/owner/repo 解析出 (owner, repo)"""
    if not url or "github.com" not in url:
        return None
    tail = url.split("github.com/", 1)[1].strip("/")
    parts = [p for p in tail.split("/") if p]
    if len(parts) < 2:
        return None
    owner, repo = parts[0], parts[1].removesuffix(".git")
    return owner, repo


def _safe_extract_tar(tar_path: Path, dest: Path) -> Path:
    """安全解包：拒绝绝对路径 / .. 穿越；跳过符号链接/硬链接；返回解包后的顶层目录"""
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    tops = set()
    safe_members = []
    with tarfile.open(tar_path, "r:gz") as tf:
        members = tf.getmembers()
        for m in members:
            name = m.name
            # 拒绝绝对路径与穿越
            if name.startswith("/") or ".." in Path(name).parts:
                raise PublishError(f"tar 成员路径越界，拒绝解包: {name}")
            # 跳过符号链接/硬链接（可能指向包外），不中止整包
            if m.issym() or m.islnk():
                logger.warning(f"tar 含链接成员，跳过: {name}")
                continue
            target = (dest / name).resolve()
            if not str(target).startswith(str(dest)):
                raise PublishError(f"tar 成员解析后越界，拒绝解包: {name}")
            if name.split("/")[0]:
                tops.add(name.split("/")[0])
            safe_members.append(m)
        tf.extractall(dest, members=safe_members)   # 只解包安全成员
    if len(tops) != 1:
        # 多顶层目录时，把 dest 本身当作素材根
        return dest
    return dest / next(iter(tops))


# ---------------------------------------------------------------
# 主体
# ---------------------------------------------------------------
class FactoryPublisher:
    """过闸货源 → 可交付成品 + 分享链接"""

    def __init__(self, work_dir: Optional[str] = None,
                 netdisk_client=None, github_token: Optional[str] = None,
                 netdisk_root: str = NETDISK_ROOT_DEFAULT,
                 enable_upload: bool = True):
        base = Path(work_dir) if work_dir else Path(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.work_dir = base / "work" / "factory_publish"
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.out_dir = base / "resources" / "packages"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.netdisk_root = netdisk_root
        self.enable_upload = enable_upload
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self._nd = netdisk_client

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UA})

        # 已发布注册表：source_url -> {netdisk_url, netdisk_pwd, shareid, ...}
        # 目的：定时任务天天跑时复用旧分享链接，避免百度分享数被耗尽（有上限）
        self.registry_path = self.out_dir / "published_registry.json"
        self.registry = self._load_registry()

        # 刷新模式：代码/文案改进后强制重下重加工重传（覆盖同名远端文件），
        # 但仍**复用旧分享链接**（新分享要占百度配额），除非实测旧链接已失效
        self.refresh = os.getenv("XIANYU_REFRESH_PACKAGES", "").lower() in ("1", "true", "yes")

    # 分享页「已死」标记 —— 百度失效/被取消的链接**同样返回 HTTP 200**，
    # 页面正文里才写「已失效」。只看状态码会把死链判成活的。
    _DEAD_MARKERS = (
        "已失效", "分享的文件已经被取消", "你访问的页面不存在",
        "分享已过期", "来晚了", "该分享已被取消", "链接不存在",
    )

    # 并发限流：避免批量复核触发百度反爬
    _SHARE_CHECK_SEMAPHORE = asyncio.Semaphore(3)
    _SHARE_CHECK_DELAY = 1.5  # 每次检查间隔

    async def _share_alive_async(self, link: str) -> bool:
        """异步复核分享链接（带并发限流）"""
        if not link:
            return False
        async with self._SHARE_CHECK_SEMAPHORE:
            await asyncio.sleep(self._SHARE_CHECK_DELAY)
            return await asyncio.to_thread(self._share_alive, link)

    def _share_alive(self, link: str) -> bool:
        """同步复核分享链接是否真能打开（不带我方 cookie）

        判据 = HTTP 200 **且** 页面无失效标记。
        （实测：重传同名文件后旧分享会失效，但状态码仍是 200）
        """
        if not link:
            return False
        try:
            r = requests.get(link, timeout=20, allow_redirects=True,
                             headers={"User-Agent": UA,
                                      "Accept-Encoding": "identity"})
            if r.status_code != 200:
                return False
            text = r.text or ""
            dead = [m for m in self._DEAD_MARKERS if m in text]
            if dead:
                logger.info(f"分享链接已失效（页面命中 {dead}）：{link}")
                return False
            return True
        except Exception as e:
            logger.info(f"分享链接复核异常（按失效处理）：{type(e).__name__}: {e}")
            return False

    # ---- 已发布注册表 ----
    REGISTRY_TTL_DAYS = 30

    def _load_registry(self) -> Dict:
        try:
            if self.registry_path.exists():
                return json.loads(self.registry_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"注册表读取失败（按空处理）: {e}")
        return {}

    def _save_registry(self):
        try:
            self.registry_path.write_text(
                json.dumps(self.registry, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"注册表写入失败: {e}")

    def _registry_hit(self, source_url: str) -> Optional[Dict]:
        """TTL 内且分享链接仍在 → 返回旧记录（复用，不重下重传重分享）"""
        rec = self.registry.get(source_url)
        if not rec or not rec.get("netdisk_url"):
            return None
        try:
            age = (datetime.now()
                   - datetime.fromisoformat(rec["published_at"])).days
        except Exception:
            return None
        if age > self.REGISTRY_TTL_DAYS:
            logger.info(f"注册表命中但已过期（{age}天 > {self.REGISTRY_TTL_DAYS}天），重新发布")
            return None
        return rec

    # 复用时要能重建**完整** manifest，所以必须把交付元数据一起持久化：
    # 交付物清单 / 加工策略 / 许可义务 / 文件数。只存链接的话，复用后
    # Phase 3 拿不到差异化信息 → 详情页会缺【我做了什么】【包含内容】【授权说明】，
    # 等于天天复用、天天把二次创作的卖点丢掉。
    _REGISTRY_KEEP = (
        "netdisk_url", "netdisk_pwd", "shareid", "fs_id", "remote_path",
        "items", "strategies", "obligations", "license_key",
        "file_count", "total_human", "dedupe_dropped", "package_bytes",
        "package_name", "package_sha256",
    )

    def _registry_record(self, source_url: str, payload: Dict):
        self.registry[source_url] = {
            **{k: payload.get(k) for k in self._REGISTRY_KEEP
               if payload.get(k) is not None},
            "published_at": datetime.now().isoformat(),
        }
        self._save_registry()

    # ---- 网盘懒加载 ----
    def _netdisk(self):
        if not self.enable_upload:
            return None
        if self._nd is None:
            backend = (os.getenv("NETDISK_BACKEND") or "").strip().lower()
            self._nd = self._make_netdisk(backend)
        return self._nd or None

    def _make_netdisk(self, backend: str):
        """选择网盘通道。

        背景（实测）：BDUSS/PCS 通道（netdisk_baidu）在账号被限制时返回
        `errno=115 账号异常，禁止分享`，重试无效；官方 bdpan OAuth 通道可正常分享。
        因此默认**优先官方通道**，不可用时回退 BDUSS。

        NETDISK_BACKEND=bdpan  -> 强制官方 OAuth 通道
        NETDISK_BACKEND=baidu  -> 强制 BDUSS/PCS 通道
        （未设置）             -> 官方优先，自动回退
        """
        if backend == "baidu":
            return self._make_baidu()

        if backend in ("", "bdpan"):
            try:
                from src.roles.product_maker.netdisk_bdpan import BdpanNetdisk, bdpan_available, bdpan_logged_in
                if bdpan_available() and bdpan_logged_in():
                    nd = BdpanNetdisk()
                    logger.info("网盘通道：官方 bdpan OAuth（作用域 /apps/bdpan/）")
                    return nd
                if backend == "bdpan":
                    logger.error("NETDISK_BACKEND=bdpan 但 bdpan 未安装/未登录")
                    return False
                logger.warning("bdpan 不可用（未安装或未登录），回退 BDUSS 通道")
            except Exception as e:
                if backend == "bdpan":
                    logger.error(f"bdpan 通道初始化失败: {e}")
                    return False
                logger.warning(f"bdpan 通道不可用，回退 BDUSS: {e}")

        return self._make_baidu()

    def _make_baidu(self):
        try:
            from src.roles.product_maker.netdisk_baidu import BaiduNetdisk
            nd = BaiduNetdisk()
            logger.info("网盘通道：BDUSS/PCS（netdisk_baidu）")
            return nd
        except Exception as e:
            logger.error(f"百度网盘(BDUSS)初始化失败，跳过上传: {e}")
            return False

    # ---- 默认分支 ----
    def _default_branch(self, owner: str, repo: str) -> str:
        hdr = {"Accept": "application/vnd.github+json"}
        if self.github_token:
            hdr["Authorization"] = f"Bearer {self.github_token}"
        try:
            r = self.session.get(f"https://api.github.com/repos/{owner}/{repo}",
                                 headers=hdr, timeout=20)
            if r.status_code == 200:
                b = r.json().get("default_branch")
                if b:
                    return b
        except Exception as e:
            logger.debug(f"取默认分支失败({owner}/{repo}): {e}")
        return "main"

    # ---- 下载 ----
    def download_repo(self, owner: str, repo: str) -> Path:
        """下载 GitHub 仓库 tarball 并安全解包，返回素材目录"""
        branch = self._default_branch(owner, repo)
        dest = self.work_dir / f"{owner}__{repo}"
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        tar_path = dest / "src.tar.gz"
        last_err = None
        for br in (branch, "main", "master"):
            url = f"https://codeload.github.com/{owner}/{repo}/tar.gz/refs/heads/{br}"
            try:
                with self.session.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True) as r:
                    if r.status_code != 200:
                        last_err = f"HTTP {r.status_code} ({br})"
                        continue
                    # 先看 content-length 封顶
                    cl = r.headers.get("Content-Length")
                    if cl and int(cl) > MAX_DOWNLOAD_BYTES:
                        raise PublishError(
                            f"仓库超过下载上限 {MAX_DOWNLOAD_BYTES // 1024 // 1024}MB: {cl} bytes")
                    got = 0
                    with open(tar_path, "wb") as f:
                        for chunk in r.iter_content(1 << 16):
                            got += len(chunk)
                            if got > MAX_DOWNLOAD_BYTES:
                                raise PublishError(
                                    f"下载超过上限 {MAX_DOWNLOAD_BYTES // 1024 // 1024}MB，中止")
                            f.write(chunk)
                if tar_path.exists() and tar_path.stat().st_size > 0:
                    root = _safe_extract_tar(tar_path, dest / "extract")
                    tar_path.unlink(missing_ok=True)
                    logger.success(f"下载解包完成: {owner}/{repo} ({got // 1024} KB)")
                    return root
            except PublishError:
                raise
            except Exception as e:
                last_err = str(e)
        raise PublishError(f"下载失败 {owner}/{repo}: {last_err}")

    # ---- 单条处理 ----
    def publish_one(self, item: Dict) -> Dict:
        """处理单条货源：重验 → 下载 → 加工 → 上传 → 分享"""
        out = dict(item)
        title = item.get("title", "<未命名>")
        category = item.get("category", "未分类")
        url = item.get("source_url") or item.get("url") or ""

        # 1) 逐条重过法律闸 —— fail-closed
        verdict = check_resource(item)
        if not verdict.sellable:
            out["publish_status"] = "rejected_at_gate"
            out["publish_error"] = "法律闸口复验拒绝: " + "; ".join(verdict.reasons)
            logger.warning(f"⛔ 复验拒绝：{title} —— {verdict.reasons}")
            return out

        # 2) 来源分流：只有 GitHub 自动下载
        if item.get("source") != "github":
            out["publish_status"] = "need_manual"
            out["publish_error"] = (
                "非 GitHub 来源（官方/政府源）不自动抓取 —— 需人工获取后再加工")
            logger.info(f"⏸ 需人工获取：{title}（source={item.get('source')}）")
            return out

        parsed = repo_from_url(url)
        if not parsed:
            out["publish_status"] = "failed"
            out["publish_error"] = f"无法解析 GitHub owner/repo: {url}"
            return out
        owner, repo = parsed

        # 2.5) 已发布去重：TTL 内复用旧分享链接（定时任务天天跑也不会吃光百度分享配额）
        cached = self._registry_hit(url)
        if cached and not self.refresh:
            out["publish_status"] = "reused"
            out["netdisk_url"] = cached.get("netdisk_url", "")
            out["netdisk_pwd"] = cached.get("netdisk_pwd", "")
            out["delivery"] = {
                **(out.get("delivery") or {}),
                # 从注册表还原交付元数据（交付物/加工策略/许可义务/文件数），
                # 否则复用后详情页会丢掉全部差异化卖点
                **{k: cached[k] for k in self._REGISTRY_KEEP if k in cached},
                "shareid": cached.get("shareid"),
                "remote_path": cached.get("remote_path"),
                "reused_from": cached.get("published_at"),
            }
            logger.info(f"♻️ 复用已有分享（免重复上传/分享）：{title} → {out['netdisk_url']}")
            return out

        try:
            # 3) 下载
            src_dir = self.download_repo(owner, repo)

            # 4) 差异化加工（四策略）
            diff = Differentiator(self.out_dir)
            res = diff.differentiate(
                [src_dir], title, category,
                sources=[{"title": title, "source_url": url,
                          "author": item.get("author", owner),
                          "license": item.get("license", "")}],
                license_key=verdict.license_key or item.get("license", ""),
                obligations=verdict.obligations or [],
            )
            zip_path = Path(res.package_path)

            out["delivery"] = {
                "package_path": str(zip_path),
                "package_bytes": zip_path.stat().st_size,
                "package_sha256": _sha256_file(zip_path),
                "file_count": res.stats.get("file_count"),
                "total_human": res.stats.get("total_human"),
                "dedupe_dropped": res.stats.get("dedupe_dropped"),
                "strategies": res.strategies,
                "applied": res.applied,
                "items": res.items,
                "license_key": res.license_key,
                "obligations": res.obligations,
            }

            # 5) 上传 + 分享
            nd = self._netdisk()
            if nd is None:
                out["publish_status"] = "packaged_no_upload"
                out["publish_error"] = "网盘未启用或不可用，已打包但未上传"
                logger.warning(f"📦 已打包未上传：{title} → {zip_path}")
                return out

            remote_dir = self.netdisk_root
            nd.makedir(remote_dir)
            up = nd.upload(str(zip_path), remote_dir=remote_dir)
            fs_id = up.get("fs_id")
            if not fs_id:
                out["publish_status"] = "failed"
                out["publish_error"] = "上传成功但未拿到 fs_id"
                logger.error(f"上传无 fs_id: {title} → {up}")
                return out

            # 关键：等待 fs_id 在索引中可见，否则 create_share 会报 31023
            if not nd.wait_fs_ready(fs_id):
                out["publish_status"] = "failed"
                out["publish_error"] = f"fs_id={fs_id} 等待就绪超时，无法创建分享"
                logger.error(f"fs_id 未就绪: {title} → {fs_id}")
                return out

            # 刷新模式下优先复用旧分享（省百度配额）—— 但必须先实测旧链接仍可访问
            reuse_share = None
            if cached and cached.get("netdisk_url") and self._share_alive(cached["netdisk_url"]):
                reuse_share = cached
                logger.info(f"♻️ 旧分享实测仍有效，复用不新建：{cached['netdisk_url']}")

            if reuse_share:
                out["delivery"].update({
                    "netdisk_url": reuse_share.get("netdisk_url", ""),
                    "netdisk_pwd": reuse_share.get("netdisk_pwd", ""),
                    "fs_id": fs_id,
                    "remote_path": up.get("path"),
                    "shareid": reuse_share.get("shareid"),
                    "share_reused": True,
                })
                out["publish_status"] = "refreshed"
            else:
                sh = nd.create_share(fs_ids=[fs_id], remote_paths=[up.get("path")],
                                     pwd=None, period=0)
                out["delivery"].update({
                    "netdisk_url": sh.get("link", ""),
                    "netdisk_pwd": sh.get("pwd", ""),
                    "fs_id": fs_id,
                    "remote_path": up.get("path"),
                    "shareid": sh.get("shareid"),
                })
                out["publish_status"] = "published"

            # 顶层别名 —— Phase 3 直接用这两个字段做发货配置
            out["netdisk_url"] = out["delivery"].get("netdisk_url", "")
            out["netdisk_pwd"] = out["delivery"].get("netdisk_pwd", "")
            logger.success(f"✅ {out['publish_status']}：{title} → "
                           f"{out['netdisk_url']} 提取码 {out['netdisk_pwd']}")
            self._registry_record(url, out["delivery"])

        except Exception as e:
            out["publish_status"] = "failed"
            out["publish_error"] = f"{type(e).__name__}: {e}"
            logger.error(f"❌ 失败：{title} —— {e}")

        return out

    # ---- 批量 ----
    def publish_manifest(self, manifest_path: str, limit: Optional[int] = None,
                         only_github: bool = False) -> Dict:
        """跑完整批，产出 deliverable_manifest_*.json"""
        items = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        if only_github:
            items = [i for i in items if i.get("source") == "github"]
        if limit:
            items = items[:limit]

        logger.info(f"=== Phase 2.5 发布器：{len(items)} 条待落地 ===")
        results: List[Dict] = []
        for i, it in enumerate(items, 1):
            logger.info(f"[{i}/{len(items)}] {it.get('title')}")
            results.append(self.publish_one(it))

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = self.out_dir / f"deliverable_manifest_{ts}.json"
        out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                            encoding="utf-8")

        from collections import Counter
        stat = Counter(r.get("publish_status") for r in results)
        report = {
            "manifest_in": str(manifest_path),
            "manifest_out": str(out_path),
            "total": len(results),
            "by_status": dict(stat),
            "published": [r for r in results if r.get("publish_status") == "published"],
        }
        logger.info(f"=== 完成：{dict(stat)} ===")
        logger.info(f"可交付清单: {out_path}")
        return report, out_path


# ---------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Phase 2.5 货源落地发布器")
    ap.add_argument("--manifest", required=True, help="sellable_manifest_*.json 路径")
    ap.add_argument("--limit", type=int, default=None, help="最多处理几条")
    ap.add_argument("--only-github", action="store_true", help="只处理 GitHub 源")
    ap.add_argument("--no-upload", action="store_true", help="只下载加工，不传网盘")
    ap.add_argument("--netdisk-root", default=NETDISK_ROOT_DEFAULT)
    args = ap.parse_args()

    pub = FactoryPublisher(enable_upload=not args.no_upload,
                           netdisk_root=args.netdisk_root)
    report, out_path = pub.publish_manifest(args.manifest, limit=args.limit,
                                           only_github=args.only_github)
    print(json.dumps({"by_status": report["by_status"],
                      "manifest_out": str(out_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

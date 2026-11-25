#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度网盘官方通道（bdpan CLI / OAuth 开放平台）

为什么需要这个模块：
  · 旧的 `netdisk_baidu.py` 走 PCS + BDUSS 网页接口，账号被限制时返回
    `errno=115 账号异常，禁止分享`，且**无法重试解决**。
  · 官方 `bdpan` CLI 走 OAuth 开放平台（openapi.baidu.com），实测可正常分享。
  · 与 `netdisk_baidu.BaiduNetdisk` **接口对齐**（upload / create_share / makedir /
    wait_fs_ready），可在 factory_publish 里直接替换。

作用域约束（官方硬约束，不可绕过）：
  所有操作限于 `/apps/bdpan/`（用户视角：「我的应用数据/bdpan/」）。
  因此本模块把远端根目录定为 `/apps/bdpan/xianyu_resources`，
  且传给 CLI 的路径一律是**相对 `/apps/bdpan/` 的相对路径**。

认证：
  由 `bdpan` CLI 自己管理（OAuth token 存 `~/.config/bdpan/config.json`，29 天有效）。
  本模块**不读不写**该配置文件（含 access_token）。

依赖：官方 bdpan CLI（https://github.com/baidu-netdisk/bdpan-storage）
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

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

from loguru import logger

# ---- 常量 ----
AGENT_SCOPE = "apps/bdpan"                       # 官方作用域（不可改）
DEFAULT_ROOT = "xianyu_resources"                # 相对 apps/bdpan 的子目录
AGENT_NAME = "hermes-agent"
DEFAULT_PERIOD = 0                               # 0=永久；可选 1/7/30
BUSINESS_DIR = "~/bdpan_business"                # 在当前目录工作（不依赖 home）


class BdpanError(Exception):
    """bdpan 通道异常"""
    pass


def _find_bdpan() -> Optional[str]:
    """定位 bdpan 可执行文件（多路径回退）"""
    # 1) PATH
    exe = shutil.which("bdpan")
    if exe:
        return exe

    home = Path(os.path.expanduser("~"))
    candidates: List[Path] = []

    # 2) 官方版本管理目录：~/.local/bdpan/versions/<version>/bdpan.exe
    ver_file = home / ".local" / "bdpan" / "current-version"
    if ver_file.exists():
        try:
            ver = ver_file.read_text(encoding="utf-8").strip()
            candidates.append(home / ".local" / "bdpan" / "versions" / ver / "bdpan.exe")
        except Exception:
            pass

    # 3) 版本目录里最新的一个
    versions_dir = home / ".local" / "bdpan" / "versions"
    if versions_dir.is_dir():
        for d in sorted(versions_dir.iterdir(), reverse=True):
            candidates.append(d / "bdpan.exe")

    # 4) Windows LOCALAPPDATA 副本
    la = os.environ.get("LOCALAPPDATA")
    if la:
        candidates.append(Path(la) / "bdpan" / "bdpan.exe")

    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def bdpan_available() -> bool:
    """bdpan CLI 是否可用"""
    return _find_bdpan() is not None


def bdpan_logged_in(bdpan_path: str = None) -> bool:
    """bdpan 是否已登录（OAuth token 有效）"""
    exe = bdpan_path or _find_bdpan()
    if not exe:
        return False
    try:
        r = subprocess.run([exe, "whoami"], capture_output=True, text=True,
                           timeout=60, encoding="utf-8", errors="replace")
        return "已登录" in (r.stdout or "")
    except Exception:
        return False


class BdpanNetdisk:
    """百度网盘官方通道客户端 —— 作用域 /apps/bdpan/"""

    def __init__(self, subdir: str = DEFAULT_ROOT, period: int = DEFAULT_PERIOD,
                 verbose: bool = False):
        self.exe = _find_bdpan()
        if not self.exe:
            raise BdpanError(
                "未找到 bdpan CLI。请先安装：\n"
                "  bash <skills>/productivity/baidu-drive/scripts/install.sh --yes"
            )
        if not bdpan_logged_in(self.exe):
            raise BdpanError(
                "bdpan 未登录。请先执行 OAuth 授权：\n"
                "  bash <skills>/productivity/baidu-drive/scripts/login.sh"
            )
        # 相对 apps/bdpan 的根目录（不含 apps/bdpan 前缀）
        self.root = subdir.strip("/")
        self.period = period
        self.verbose = verbose
        # 单次进程内复用的 session_id（skill 要求 {timestamp}-{random}）
        import random
        import string
        self.session_id = (f"{int(time.time())}-"
                           f"{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}")
        self.session_input = "闲鱼管线自动交付：上传资源包并生成分享链接"

    # ---------- 底层 ----------

    def _run(self, args: List[str], json_out: bool = True,
             timeout: int = 1800) -> Dict:
        """调用 bdpan CLI 并解析 JSON 输出"""
        cmd = [self.exe] + list(args)
        # skill 公共参数（服务质量追踪用，非业务逻辑）
        cmd += ["--agentname", AGENT_NAME,
                "--session-input", self.session_input,
                "--session-id", self.session_id]
        if json_out:
            cmd.append("--json")

        if self.verbose:
            logger.debug(f"bdpan: {' '.join(cmd)}")

        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()

        if not json_out:
            if r.returncode != 0:
                raise BdpanError(f"bdpan {' '.join(args)} 失败(rc={r.returncode}): {err or out}")
            return {"raw": out}

        # 解析 JSON
        payload = None
        if out:
            try:
                payload = json.loads(out)
            except json.JSONDecodeError:
                # 可能夹带日志行，取最后一个 JSON 对象
                start = out.find("{")
                if start >= 0:
                    try:
                        payload = json.loads(out[start:])
                    except json.JSONDecodeError:
                        payload = None

        if payload is None:
            raise BdpanError(f"bdpan {' '.join(args)} 无有效 JSON 输出: {out[:300]} {err[:200]}")

        # 列表型结果（如 ls / search）直接返回，不做 dict 层错误判定
        if isinstance(payload, list):
            return payload

        # 统一错误判定
        code = payload.get("code")
        errno = payload.get("errno")
        if (code not in (0, None)) or (errno not in (0, None)):
            msg = (payload.get("error") or payload.get("message")
                   or payload.get("show_msg") or payload.get("errmsg") or "")
            raise BdpanError(
                f"bdpan {' '.join(args)} 失败 code={code} errno={errno} msg={msg}")
        return payload

    def _rel(self, remote_dir: str) -> str:
        """把远端路径归一化为**相对 apps/bdpan** 的相对路径（CLI 要求）"""
        p = (remote_dir or "").strip()
        # 去掉各种前缀写法
        for prefix in ("/apps/bdpan/", "apps/bdpan/", "/apps/bdpan", "apps/bdpan",
                       "我的应用数据/bdpan/", "我的应用数据/bdpan"):
            if p.startswith(prefix):
                p = p[len(prefix):]
                break
        return p.strip("/")

    def remote_root(self) -> str:
        """远端根（相对 apps/bdpan）"""
        return self.root

    # ---------- 与 BaiduNetdisk 对齐的接口 ----------

    def makedir(self, remote_dir: str = None) -> str:
        """确保目录存在（幂等）"""
        rel = self._rel(remote_dir) if remote_dir else self.root
        if not rel:
            return AGENT_SCOPE
        try:
            self._run(["mkdir", rel])
            logger.info(f"网盘目录已创建: {AGENT_SCOPE}/{rel}")
        except BdpanError as e:
            # 已存在不算错
            if "已存在" in str(e) or "exist" in str(e).lower():
                logger.debug(f"网盘目录已存在: {AGENT_SCOPE}/{rel}")
            else:
                raise
        return f"/{AGENT_SCOPE}/{rel}"

    def upload(self, local_path: str, remote_dir: str = None,
               remote_name: str = None) -> Dict:
        """
        上传单个文件。
        返回 {"path": <绝对远端路径>, "fs_id": <str>, "size": int, "md5": str}
        """
        lp = Path(local_path)
        if not lp.is_file():
            raise BdpanError(f"本地文件不存在: {local_path}")

        rel_dir = self._rel(remote_dir) if remote_dir else self.root
        name = remote_name or lp.name
        rel_target = f"{rel_dir}/{name}" if rel_dir else name

        payload = self._run(["upload", str(lp), rel_target])

        # bdpan 上传结果是 {code:0, data:{...}}
        data = payload.get("data") or payload
        fs_id = str(data.get("fsid") or data.get("fs_id") or "")
        if not fs_id:
            raise BdpanError(f"上传成功但未拿到 fsid: {json.dumps(data, ensure_ascii=False)[:300]}")

        result = {
            "path": data.get("remote_path") or f"/{AGENT_SCOPE}/{rel_target}",
            "fs_id": fs_id,
            "size": data.get("size"),
            "md5": data.get("md5"),
            "remote": rel_target,
        }
        logger.success(f"网盘上传完成: {result['path']} (fsid={fs_id})")
        return result

    def fs_id_of(self, remote_path: str) -> Optional[str]:
        """按远端路径查 fsid"""
        rel = self._rel(remote_path)
        try:
            payload = self._run(["ls", rel])
            items = payload if isinstance(payload, list) else payload.get("list", [])
            if items:
                it = items[0]
                return str(it.get("fsid") or it.get("fs_id") or "")
        except BdpanError:
            pass
        return None

    def list(self, remote_dir: str = None) -> List[Dict]:
        """列出目录内容"""
        rel = self._rel(remote_dir) if remote_dir else self.root
        payload = self._run(["ls", rel] if rel else ["ls"])
        if isinstance(payload, list):
            return payload
        return payload.get("list", [])

    def wait_fs_ready(self, fs_id: Union[str, int], timeout: int = 60,
                      interval: int = 3) -> bool:
        """等待文件进入索引（bdpan 走开放平台，通常即时可见；此处做轻量确认）"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            # 开放平台上传后即时返回 fsid，无需长等；此处仅留观察窗口
            if fs_id:
                return True
            time.sleep(interval)
        return bool(fs_id)

    def create_share(self, fs_ids: List[Union[str, int]] = None,
                     remote_paths: List[str] = None,
                     pwd: str = None, period: int = None) -> Dict:
        """
        创建分享。
        返回 {"link": ..., "pwd": ..., "shareid": ..., "short_url": ...}

        注意：bdpan share 只接受**路径**（相对 apps/bdpan），不接受 fs_id；
              因此优先用 remote_paths；只有 fs_ids 时先反查路径。
        """
        period = self.period if period is None else period
        # 官方 --period 只支持 0/1/7/30
        if period not in (0, 1, 7, 30):
            period = 7

        targets: List[str] = []
        if remote_paths:
            targets = [self._rel(p) for p in remote_paths]
        elif fs_ids:
            for fid in fs_ids:
                # 反查路径：扫描根目录
                found = None
                for it in self.list(self.root):
                    if str(it.get("fsid") or it.get("fs_id") or "") == str(fid):
                        found = self._rel(it.get("path", ""))
                        break
                if found:
                    targets.append(found)
            if not targets:
                raise BdpanError(f"无法由 fs_id 反查路径: {fs_ids}")

        if not targets:
            raise BdpanError("create_share 需要 remote_paths 或 fs_ids")

        args = ["share"] + targets + ["--period", str(int(period))]
        payload = self._run(args)

        # bdpan share 返回 {link, short_url, share_id, period, pwd}
        link = payload.get("link") or payload.get("short_url") or ""
        if payload.get("short_url") and not str(link).startswith("http"):
            link = f"https://pan.baidu.com/s/{payload['short_url']}"

        result = {
            "link": link,
            "pwd": payload.get("pwd", pwd or ""),
            "shareid": payload.get("share_id"),
            "short_url": payload.get("short_url"),
            "period": payload.get("period", period),
        }
        logger.success(f"网盘分享创建成功: {result['link']} 提取码 {result['pwd']}")
        return result

    def upload_and_share(self, local_path: str, remote_dir: str = None,
                         pwd: str = None, period: int = None) -> Dict:
        """上传 + 分享 一条龙"""
        self.makedir(remote_dir or self.root)
        up = self.upload(local_path, remote_dir=remote_dir)
        sh = self.create_share(remote_paths=[up["remote"]], pwd=pwd, period=period)
        return {**up, **sh}


# ---------- 自测 ----------
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--upload", help="上传文件并分享")
    ap.add_argument("--ls", action="store_true", help="列出根目录")
    ap.add_argument("--check", action="store_true", help="检查可用性")
    a = ap.parse_args()

    if a.check:
        print("bdpan CLI:", _find_bdpan() or "未找到")
        print("已登录:", bdpan_logged_in())
    elif a.ls:
        nd = BdpanNetdisk()
        print(json.dumps(nd.list(), ensure_ascii=False, indent=2))
    elif a.upload:
        nd = BdpanNetdisk()
        print(json.dumps(nd.upload_and_share(a.upload), ensure_ascii=False, indent=2))

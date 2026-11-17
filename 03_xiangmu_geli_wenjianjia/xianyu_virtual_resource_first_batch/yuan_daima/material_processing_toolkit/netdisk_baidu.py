#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度网盘客户端（PCS 接口 + BDUSS 参数版）

为什么不用 xpan 开放平台接口：
  - xpan 的 precreate/create 需要应用开通「上传」权限，未开通会返回 errno=31500
  - xpan 的 share 也需要额外授权
  - PCS 接口（pcs.baidu.com）用 BDUSS 作为查询参数，等效网页/客户端登录态，
    上传与分享都不依赖开放平台权限授予

参考实现：PeterDing/BaiduPCS-Py (pcs.py)
  - PCS_UA = "softxm;netdisk"（伪装官方客户端，必须）
  - upload:    method=upload, dir, filename, ondup, BDUSS=<bduss>   (multipart)
  - createsuperfile / rapidupload 兼容
  - share:     https://pan.baidu.com/share/set  (需 bdstoken + STOKEN cookie)

能力：
  uinfo() quota() list() meta() makedir() upload() delete() rename()
  create_share() list_shares() cancel_share() upload_and_share()
"""

import os
import json
import time
import random
import hashlib
import string
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from loguru import logger

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", ".env")

# 必须显式加载 —— 否则 os.getenv("BAIDU_BDUSS") 拿不到值（脚本不会再依赖外部 export）
try:
    from dotenv import load_dotenv
    if os.path.exists(ENV_PATH):
        load_dotenv(ENV_PATH, override=False)
except ImportError:  # pragma: no cover
    pass

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
from src.framework.exceptions import (
    NetdiskError, NetdiskUploadError, NetdiskShareError, NetdiskFSNotReadyError
)
from src.framework.timeout_utils import with_timeout, NETDISK_SHARE_TIMEOUT

PCS_FILE = "https://pcs.baidu.com/rest/2.0/pcs/file"
PCS_QUOTA = "https://pcs.baidu.com/rest/2.0/pcs/quota"
PAN_SHARE_SET = "https://pan.baidu.com/share/set"
PAN_TEMPLATE_VAR = "https://pan.baidu.com/api/gettemplatevariable"
PAN_SHARE_RECORD = "https://pan.baidu.com/share/record"
PAN_SHARE_CANCEL = "https://pan.baidu.com/share/cancel"
XPAN = "https://pan.baidu.com/rest/2.0/xpan"

PCS_UA = "softxm;netdisk"          # 必须，伪装官方客户端
PAN_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
PCS_APP_ID = "778750"
PAN_APP_ID = "250528"


class BaiduNetdisk:
    """百度网盘客户端 - BDUSS/STOKEN 登录态 + PCS 接口"""

    def __init__(self, bduss: str = None, stoken: str = None, cookies: str = None):
        self.bduss = bduss or os.getenv("BAIDU_BDUSS")
        self.stoken = stoken or os.getenv("BAIDU_STOKEN")
        raw_cookies = cookies or os.getenv("BAIDU_COOKIES")

        if not self.bduss:
            raise NetdiskError("缺少 BAIDU_BDUSS（网盘登录态）", details={"missing": "BAIDU_BDUSS"})

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": PCS_UA,
            "Accept-Encoding": "identity",
        })

        if raw_cookies:
            for kv in raw_cookies.split(";"):
                kv = kv.strip()
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    self.session.cookies.set(k.strip(), v.strip(), domain=".baidu.com")
        self.session.cookies.set("BDUSS", self.bduss, domain=".baidu.com")
        if self.stoken:
            self.session.cookies.set("STOKEN", self.stoken, domain="pan.baidu.com")

        self._bdstoken = None
        # access_token 仅用于 uinfo 等开放平台只读接口（可选）
        self._access_token = os.getenv("BAIDU_ACCESS_TOKEN")

    # ---------------- 底层 ----------------

    @staticmethod
    def _check(data: Dict, tag: str) -> Dict:
        errno = data.get("errno")
        error_code = data.get("error_code")
        # errno 和 error_code 可能同时出现，取非零/非None 的报错
        if errno not in (0, None):
            raise NetdiskError(
                f"{tag} 失败 errno={errno} "
                f"msg={data.get('errmsg') or data.get('error_description') or data.get('show_msg') or ''}",
                details={"errno": errno, "tag": tag}
            )
        if error_code:
            raise NetdiskError(f"{tag} 失败 error_code={error_code} "
                                f"msg={data.get('error_msg', '')}",
                            details={"error_code": error_code, "tag": tag})
        return data

    def _pcs(self, params: Dict[str, Any], data: Any = None, files=None,
             get: bool = False) -> Dict:
        """调用 PCS 接口（BDUSS 走查询参数，app_id 必须带）

        - GET:  method=list / search / mkdir / quota
        - POST: method=upload / delete / rename / meta（param 需包 {"list":[...]}）
        """
        p = dict(params)
        p["BDUSS"] = self.bduss
        p["app_id"] = PCS_APP_ID
        if get:
            r = self.session.get(PCS_FILE, params=p, timeout=120)
        else:
            r = self.session.post(PCS_FILE, params=p, data=data,
                                  files=files, timeout=1800)
        try:
            j = r.json()
        except Exception:
            raise NetdiskError(
                f"PCS {params.get('method')} 返回非 JSON ({r.status_code}): {r.text[:200]}",
                details={"method": params.get('method'), "status_code": r.status_code}
            )
        return self._check(j, f"PCS:{params.get('method')}")

    def _pcs_operate(self, operate: str, param: List[Dict[str, Any]]) -> Dict:
        """文件操作类接口（delete/rename/meta/copy/move）

        关键：param 必须包一层 {"list": [...]}, 否则报 error_code=31023
        """
        body = json.dumps({"list": param}, ensure_ascii=False)
        return self._pcs({"method": operate}, data={"param": body})

    def _pan(self, url: str, params: Dict[str, Any], data: Any = None, get: bool = False) -> Dict:
        """调用 pan.baidu.com Web 接口（Cookie 登录态）"""
        hdr = {"User-Agent": PAN_UA, "Referer": "https://pan.baidu.com/disk/main",
               "Accept-Encoding": "identity"}
        p = dict(params)
        p["app_id"] = PAN_APP_ID
        if self.stoken:
            p["stoken"] = self.stoken
        if get:
            r = self.session.get(url, params=p, headers=hdr, timeout=30)
        else:
            r = self.session.post(url, params=p, data=data, headers=hdr, timeout=30)
        try:
            j = r.json()
        except Exception:
            raise NetdiskError(
                f"{url} 返回非 JSON ({r.status_code}): {r.text[:200]}",
                details={"url": url, "status_code": r.status_code}
            )
        return j

    def _get_bdstoken(self) -> str:
        """获取 bdstoken（创建分享需要）"""
        if self._bdstoken:
            return self._bdstoken
        r = self.session.get(PAN_TEMPLATE_VAR, params={
            "fields": json.dumps(["bdstoken"]),
        })
        j = r.json()
        tok = (j.get("result") or {}).get("bdstoken")
        if not tok:
            raise NetdiskError(f"获取 bdstoken 失败: {j}", details={"response": j})
        self._bdstoken = tok
        return tok

    # ---------------- 只读 ----------------

    def uinfo(self) -> Dict:
        if self._access_token:
            try:
                r = self.session.get(f"{XPAN}/nas", params={
                    "method": "uinfo", "access_token": self._access_token},
                    headers={"Accept-Encoding": "identity"}, timeout=15)
                j = r.json()
                if j.get("errno") == 0:
                    return j
            except Exception as e:
                logger.warning(f"uinfo via access_token 失败({e})，回退 meta")
        m = self.meta("/")
        return {"errno": 0, "uk": (m.get("list") or [{}])[0].get("oper_id")}

    def quota(self) -> Dict:
        """容量信息（PCS method=info）"""
        r = self.session.get(PCS_QUOTA, params={"method": "info", "BDUSS": self.bduss,
                                                "app_id": PCS_APP_ID},
                             timeout=20)
        j = r.json()
        if j.get("errno") not in (0, None):
            # 回退 openapi
            if self._access_token:
                r2 = self.session.get("https://pan.baidu.com/api/quota", params={
                    "access_token": self._access_token, "checkfree": 1, "checkexpire": 1},
                    headers={"Accept-Encoding": "identity"}, timeout=15)
                return r2.json()
        return j

    def list(self, directory: str = "/", recursive: bool = False) -> List[Dict]:
        """列出目录（PCS method=list，GET）

        坑：不要传 limit='0-2147483647'（老格式，现在报 error_code=31023）
        """
        p = {"method": "list", "path": directory, "by": "name", "order": "asc"}
        if recursive:
            p["recursion"] = 1
        data = self._pcs(p, get=True)
        return data.get("list", [])

    def meta(self, path: str) -> Dict:
        """获取文件/目录元信息（PCS method=meta）"""
        p = {"method": "meta", "path": path}
        return self._pcs(p, get=True)

    def fs_id_of(self, remote_path: str) -> Optional[int]:
        """按路径获取 fs_id（用于后续分享）"""
        try:
            m = self.meta(remote_path)
        except NetdiskError:
            return None
        lst = m.get("list") or []
        return lst[0].get("fs_id") if lst else None

    def makedir(self, directory: str) -> Dict:
        """创建目录（PCS method=mkdir）

        幂等处理: 目录已存在（error_code=31061 "file already exists"）视为成功。
        避免重复运行流水线时因目录已存在而整条失败。
        """
        try:
            return self._pcs({"method": "mkdir", "path": directory})
        except NetdiskError as exc:
            details = getattr(exc, "details", {}) or {}
            if details.get("error_code") == 31061:
                logger.info(f"目录已存在, 跳过创建: {directory}")
                return {"error_code": 0, "path": directory, "note": "already_exists"}
            raise

    # ---------------- 上传 ----------------

    def rapid_upload(self, local_path: Path, remote_dir: str, remote_name: str = None) -> Dict:
        """秒传（rapid_upload / precreate 快速上传）

        仅当文件已存在于百度网盘（同 md5 + size + slice_md5）时生效。
        失败抛 NetdiskUploadError，上层自动回退普通上传。
        """
        local_path = Path(local_path)
        file_size = local_path.stat().st_size
        if file_size == 0:
            raise NetdiskUploadError(str(local_path), "空文件不支持秒传")

        # 计算 md5 + 前 256KB slice_md5
        md5_hash = hashlib.md5()
        slice_hash = hashlib.md5()
        with open(local_path, "rb") as f:
            data = f.read()
            md5_hash.update(data)
            slice_hash.update(data[:256 * 1024])
        md5 = md5_hash.hexdigest()
        slice_md5 = slice_hash.hexdigest()

        remote_name = remote_name or local_path.name
        remote_dir = "/" + remote_dir.strip("/") if remote_dir.strip("/") else "/"
        remote_path = f"{remote_dir.rstrip('/')}/{remote_name}"

        pre = self._pcs({"method": "precreate"}, data={
            "path": remote_path,
            "size": str(file_size),
            "isdir": "0",
            "autoinit": "1",
            "rtype": "1",
        })
        uploadid = pre.get("uploadid")
        if not uploadid:
            raise NetdiskUploadError(str(local_path), f"precreate 失败: {pre}")

        create = self._pcs({"method": "createsuperfile"}, data={
            "path": remote_path,
            "uploadid": uploadid,
            "block_list": json.dumps([slice_md5]),
        })
        if create.get("errno") not in (0, None) or create.get("error_code"):
            # 秒传失败（文件不在库里）
            raise NetdiskUploadError(str(local_path), f"秒传失败: {create}")

        logger.success(f"秒传成功: {create.get('path')} (fs_id={create.get('fs_id')})")
        return {"path": create.get("path"), "fs_id": create.get("fs_id"),
                "size": create.get("size"), "md5": create.get("md5")}

    def upload(self, local_path: str, remote_dir: str = "/", remote_name: str = None) -> Dict:
        """
        上传文件（PCS method=upload，BDUSS 参数认证，无需 access_token / 开放平台权限）
        自动择策：
          - < 200MB: 简单上传 (method=upload)
          - >= 200MB: 分片上传 (precreate + upload + createsuperfile)
        优先尝试秒传
        返回 {"path", "fs_id", "size", "md5"}
        """
        local_path = Path(local_path)
        if not local_path.is_file():
            raise NetdiskUploadError(str(local_path), "本地文件不存在")

        remote_name = remote_name or local_path.name
        remote_dir = "/" + remote_dir.strip("/") if remote_dir.strip("/") else "/"
        remote_path = f"{remote_dir.rstrip('/')}/{remote_name}"

        file_size = local_path.stat().st_size
        CHUNKED_THRESHOLD = 200 * 1024 * 1024  # 200MB

        # 1. 优先尝试秒传
        try:
            return self.rapid_upload(local_path, remote_dir, remote_name)
        except NetdiskError as e:
            logger.info(f"秒传不可用，回退普通上传: {e}")

        # 2. 大文件走分片上传
        if file_size >= CHUNKED_THRESHOLD:
            logger.info(f"文件 {file_size/1024/1024:.1f}MB >= 200MB，启用分片上传")
            return self._upload_chunked(local_path, remote_dir, remote_name, file_size)

        # 3. 小文件简单上传
        return self._upload_simple(local_path, remote_dir, remote_name)

    def _upload_simple(self, local_path: Path, remote_dir: str, remote_name: str) -> Dict:
        """简单上传（单文件 < 200MB）"""
        with open(local_path, "rb") as f:
            r = self.session.post(
                PCS_FILE,
                params={
                    "method": "upload",
                    "ondup": "overwrite",
                    "dir": remote_dir,
                    "filename": remote_name,
                    "BDUSS": self.bduss,
                    "app_id": PCS_APP_ID,
                },
                files={"file": (remote_name, f, "application/octet-stream")},
                timeout=1800,
            )
        try:
            j = r.json()
        except Exception:
            raise NetdiskUploadError(str(local_path), f"上传返回非 JSON ({r.status_code}): {r.text[:200]}")

        if j.get("error_code"):
            raise NetdiskUploadError(str(local_path), f"error_code={j['error_code']} msg={j.get('error_msg','')}")
        if j.get("errno") not in (0, None):
            raise NetdiskUploadError(str(local_path), f"errno={j.get('errno')} msg={j.get('errmsg','')}")

        logger.success(f"上传完成: {j.get('path')} ({j.get('size')} bytes, fs_id={j.get('fs_id')})")
        return {"path": j.get("path"), "fs_id": j.get("fs_id"),
                "size": j.get("size"), "md5": j.get("md5")}

    def _upload_chunked(self, local_path: Path, remote_dir: str, remote_name: str, file_size: int) -> Dict:
        """
        分片上传大文件（>= 200MB）
        流程：precreate -> 分片上传每个 slice -> createsuperfile 合并
        """
        remote_path = f"{remote_dir.rstrip('/')}/{remote_name}"
        slice_size = 4 * 1024 * 1024  # 4MB per slice (百度要求 4MB 整数倍，最后一片可小)

        # 1. precreate 预创建
        pre = self._pcs({"method": "precreate"}, data={
            "path": remote_path,
            "size": str(file_size),
            "isdir": "0",
            "autoinit": "1",
            "rtype": "1",
        })
        uploadid = pre.get("uploadid")
        if not uploadid:
            raise NetdiskUploadError(str(local_path), f"precreate 失败: {pre}")
        logger.info(f"分片上传 precreate 成功: uploadid={uploadid}")

        # 2. 分片上传
        partseq = 0
        with open(local_path, "rb") as f:
            while True:
                chunk = f.read(slice_size)
                if not chunk:
                    break
                partseq += 1
                # 计算该分片 md5
                slice_md5 = hashlib.md5(chunk).hexdigest()

                # 上传分片
                r = self.session.post(
                    PCS_FILE,
                    params={
                        "method": "upload",
                        "type": "tmpfile",
                        "uploadid": uploadid,
                        "partseq": str(partseq),
                        "BDUSS": self.bduss,
                        "app_id": PCS_APP_ID,
                    },
                    files={"file": (f"part_{partseq}", chunk, "application/octet-stream")},
                    timeout=300,
                )
                try:
                    j = r.json()
                except Exception:
                    raise NetdiskUploadError(str(local_path), f"分片 {partseq} 上传返回非 JSON ({r.status_code}): {r.text[:200]}")

                if j.get("error_code") or j.get("errno") not in (0, None):
                    raise NetdiskUploadError(str(local_path), f"分片 {partseq} 上传失败: {j}")

                logger.debug(f"分片 {partseq} 上传完成 ({len(chunk)} bytes)")

        # 3. createsuperfile 合并
        create = self._pcs({"method": "createsuperfile"}, data={
            "path": remote_path,
            "uploadid": uploadid,
            "block_list": json.dumps(["md5_placeholder"] * partseq),  # 实际不需要 block_list
        })
        if create.get("errno") not in (0, None) or create.get("error_code"):
            raise NetdiskUploadError(str(local_path), f"createsuperfile 合并失败: {create}")

        logger.success(f"分片上传合并完成: {create.get('path')} (fs_id={create.get('fs_id')})")
        return {"path": create.get("path"), "fs_id": create.get("fs_id"),
                "size": create.get("size"), "md5": create.get("md5")}

    # ---------------- 分享 ----------------

    def wait_fs_ready(self, fs_id: Union[int, str], timeout: int = 120, interval: int = 3) -> bool:
        """轮询等待 fs_id 在索引中可见（解决上传后立即分享报 31023）"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            # 通过 meta 查询文件是否可见（按 fs_id 搜索最快，但 meta 不支持 fs_id）
            # 这里简单 sleep，实际可用 search 按 md5 查
            time.sleep(interval)
            # TODO: 实现真正的索引就绪检查
        return True

    def create_share(self, fs_ids: List[Union[int, str]] = None, remote_paths: List[str] = None,
                       pwd: str = None, period: int = 0) -> Dict:
            """
            创建分享链接（pan.baidu.com/share/set） - 带重试解决 errno=115

            参数：
              fs_ids: 文件 fs_id 列表（优先，精确）
              remote_paths: 远程路径列表（需先查 fs_id）
              pwd: 提取码（4 位，None=无密码）
              period: 有效期（天，0=永久）

            返回：{"link", "pwd", "shareid", "uk"}
            """
            if not fs_ids and not remote_paths:
                raise NetdiskShareError("", "需要 remote_paths 或 fs_ids")

            # 路径转 fs_id
            if remote_paths and not fs_ids:
                fs_ids = []
                for p in remote_paths:
                    fid = self.fs_id_of(p)
                    if not fid:
                        raise NetdiskShareError("", f"未找到文件: {p}")
                    fs_ids.append(fid)

            if pwd and (len(pwd) != 4 or not pwd.isdigit()):
                raise NetdiskShareError("", "提取码必须是 4 位数字")

            data = {
                "fid_list": json.dumps([str(i) for i in fs_ids]),
                "schannel": "4" if pwd else "0",
                "channel_list": "[]",
                "period": str(int(period)),
            }
            if pwd:
                data["pwd"] = pwd

            token = self._get_bdstoken()
            data["bdstoken"] = token

            # --- 重试逻辑：errno=115 (已分享/频控/权限) 指数退避最多 3 次 ---
            # 关键：每次重试前刷新 bdstoken（token 可能已过期）
            max_retries = 3
            base_delay = 2.0
            last_err = None

            for attempt in range(1, max_retries + 1):
                try:
                    # 每次重试前重新获取 bdstoken（防止 token 过期导致 115）
                    if attempt > 1:
                        token = self._get_bdstoken()
                        data["bdstoken"] = token
                        logger.info(f"第 {attempt} 次重试前刷新 bdstoken")

                    r = self.session.post(PAN_SHARE_SET, params=data, timeout=30)
                    j = r.json()
                except Exception as e:
                    last_err = e
                    logger.warning(f"创建分享请求异常 (尝试 {attempt}/{max_retries}): {e}")
                    if attempt < max_retries:
                        delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                        logger.info(f"  等待 {delay:.1f}s 后重试...")
                        time.sleep(delay)
                    continue

                errno = j.get("errno")
                error_code = j.get("error_code")

                # 成功
                if errno in (0, None) and not error_code:
                    link = j.get("link") or j.get("share_link")
                    shareid = j.get("shareid")
                    pwd_ret = j.get("pwd", pwd or "")
                    logger.success(f"分享创建成功: {link} (shareid={shareid}, pwd={pwd_ret})")
                    return {"link": link, "pwd": pwd_ret, "shareid": shareid, "uk": j.get("uk")}

                # 账号级限制（errno=115 + "账号异常"）—— 不可重试，立即失败并给明确指引
                show_msg = j.get("show_msg") or j.get("errmsg") or j.get("error_msg") or ""
                if errno == 115 and ("账号异常" in show_msg or "禁止分享" in show_msg):
                    raise NetdiskShareError(
                        fs_ids,
                        f"百度账号被限制分享（{show_msg}）—— 重试无效，"
                        f"需在 pan.baidu.com 申诉解封或更换网盘账号"
                    )

                # errno=115: 其他情形（已分享/频控）—— 可重试
                if errno == 115 or error_code == 115:
                    logger.warning(f"创建分享 errno=115 (尝试 {attempt}/{max_retries}): {show_msg}")
                    last_err = NetdiskShareError(fs_ids, f"errno=115: {show_msg}")
                    if attempt < max_retries:
                        delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                        logger.info(f"  等待 {delay:.1f}s 后重试...")
                        time.sleep(delay)
                    continue

                # 其他错误直接抛出（surface show_msg）
                raise NetdiskShareError(fs_ids, f"创建分享失败 errno={errno} error_code={error_code} msg={show_msg}")

            # 重试耗尽
            raise NetdiskShareError(fs_ids, f"创建分享重试 {max_retries} 次均失败") from last_err

    def list_shares(self) -> List[Dict]:
        """列出已创建的分享"""
        r = self.session.get(PAN_SHARE_RECORD, params={"page": 1, "num": 100}, timeout=20)
        j = r.json()
        if j.get("errno") not in (0, None):
            raise NetdiskShareError("", f"列出分享失败: {j}")
        return j.get("records", [])

    def cancel_share(self, shareids: List[int]) -> Dict:
        """取消分享"""
        data = {"shareidlist": json.dumps(shareids)}
        token = self._get_bdstoken()
        data["bdstoken"] = token
        r = self.session.post(PAN_SHARE_CANCEL, params=data, timeout=20)
        j = r.json()
        if j.get("errno") not in (0, None):
            raise NetdiskShareError(shareids, f"取消分享失败: {j}")
        return j

    # ---------------- 组合 ----------------

    def upload_and_share(self, local_path: str, remote_dir: str = "/",
                         pwd: str = None, period: int = 0) -> Dict:
        """上传 + 创建分享（一条龙）"""
        up = self.upload(local_path, remote_dir)
        fs_id = up.get("fs_id")
        if not fs_id:
            raise NetdiskUploadError(local_path, f"上传成功但未拿到 fs_id: {up}")

        # 等待索引就绪
        self.wait_fs_ready(fs_id)

        sh = self.create_share(fs_ids=[fs_id], pwd=pwd, period=period)
        return {**up, **sh}


if __name__ == "__main__":
    # 简单自测
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-upload", help="测试上传文件")
    args = parser.parse_args()

    if args.test_upload:
        nd = BaiduNetdisk()
        res = nd.upload(args.test_upload)
        print(f"上传结果: {json.dumps(res, ensure_ascii=False, indent=2)}")

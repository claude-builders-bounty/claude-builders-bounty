"""
GitHub 公开 bounty issues 适配器 (零凭据、零成本)

通过 GitHub 公开 REST API 发现带 bounty 标签的开放 Issue。
不登录、不绕过风控、不抓取需认证页面，所有目标均为公开可访问资源。

支持任务提交：在 github_bounties_public 平台上找到的任务，通过 GitHub PR 方式提交成果。
"""

import asyncio
import json
import logging
import re
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

from adapters.base import (
    PlatformAdapter, TaskInfo, SubmissionResult, WithdrawalResult,
    AccountInfo, Track, TaskStatus, register_adapter,
)

logger = logging.getLogger("adapters.github_bounties_public")


@register_adapter("github_bounties_public")
class GitHubBountiesPublicAdapter(PlatformAdapter):
    """GitHub 公开 bounty 适配器 (零凭据)"""

    PLATFORM_NAME = "github_bounties_public"
    SUPPORTED_TRACKS = [
        Track.ALGORITHM, Track.DATA_ANALYSIS, Track.FRONTEND,
        Track.SMART_CONTRACT, Track.DOCS, Track.TESTING,
    ]
    REQUIRES_BROWSER = False

    GITHUB_SEARCH_URL = "https://api.github.com/search/issues"
    GITHUB_PER_PAGE = 30

    # 奖金提取正则 (从 issue 正文/标题)
    REWARD_PATTERNS = [
        re.compile(r"\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:bounty|reward|prize|usd)", re.IGNORECASE),
        re.compile(r"(?:bounty|reward|prize).*?\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)", re.IGNORECASE),
        re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:USD|US\$|\$)", re.IGNORECASE),
    ]

    def __init__(self, credentials: Dict[str, str], config: Optional[Dict] = None):
        super().__init__(credentials, config)
        creds: Dict[str, str] = credentials or {}
        cfg: Dict[str, Any] = config or {}
        self._session_timeout = cfg.get("session_timeout", 20)
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl_seconds = 300
        self._rate_limited_until: Optional[datetime] = None
        self._authenticated = False  # 零凭据模式，不需要认证

    @property
    def platform_name(self) -> str:
        return self.PLATFORM_NAME

    @property
    def supported_tracks(self) -> List[Track]:
        return self.SUPPORTED_TRACKS

    async def authenticate(self) -> bool:
        """零凭据模式：无需认证，直接返回 True"""
        self._authenticated = True
        logger.info(f"{self.platform_name} 零凭据模式，认证跳过")
        return True

    async def discover_tasks(self, filters: Dict[str, Any]) -> List[TaskInfo]:
        """发现 GitHub 公开 bounty 任务"""
        filters = filters or {}
        results: List[TaskInfo] = []

        coros = [
            self._discover_github_bounties(filters, track=track)
            for track in Track
        ]
        try:
            source_results = await asyncio.gather(*coros, return_exceptions=True)
            for track, res in zip([t.value for t in Track], source_results):
                if isinstance(res, Exception):
                    logger.warning("[公开发现] 源 github(%s) 异常: %s", track, res)
                    continue
                if isinstance(res, list):
                    results.extend(res)
        except Exception as exc:
            logger.exception("[公开发现] 并发发现异常: %s", exc)

        # 去重
        seen: set[str] = set()
        unique: List[TaskInfo] = []
        for t in results:
            if t.platform_task_id in seen:
                continue
            seen.add(t.platform_task_id)
            unique.append(t)

        logger.info("[公开发现] 共发现 %d 个任务 (去重后 %d 个)", len(results), len(unique))
        return unique

    async def _discover_github_bounties(
        self, filters: Dict[str, Any], track: Optional[Track] = None
    ) -> List[TaskInfo]:
        """抓取 GitHub 公开 API 的 bounty issues"""
        tasks: List[TaskInfo] = []

        if filters.get("track") and track != filters["track"]:
            return tasks

        terms = ["bounty", "is:open", "is:issue"]
        if track:
            terms.extend(self._track_keywords(track))
        if filters.get("keywords"):
            terms.extend(filters["keywords"])
        terms = list(dict.fromkeys(terms))
        query = " ".join(terms)

        url = self._build_github_url(query)
        try:
            items = await self._fetch_json_list(url)
        except Exception as exc:
            logger.warning("[公开发现] GitHub 抓取失败 (track=%s): %s", track, exc)
            return tasks

        for item in items:
            try:
                title = item.get("title") or ""
                body = item.get("body") or ""
                html_url = item.get("html_url") or ""
                number = item.get("number")
                created_at = item.get("created_at")

                # 合规扫描 (文本)
                text = f"{title} {body} {html_url}"
                if self._matches_reject(text):
                    logger.debug("[公开发现] 跳过命中红线: %s", title[:60])
                    continue

                reward_amount = self._extract_reward(title, body)
                if filters.get("min_reward") is not None and reward_amount < filters["min_reward"]:
                    continue

                task_track = track if track else self._infer_track(title, body)
                if filters.get("track") and task_track != filters["track"]:
                    continue

                platform_task_id = f"github-{number}" if number is not None else html_url

                deadline = self._parse_deadline(created_at)

                task = TaskInfo(
                    platform_task_id=platform_task_id,
                    title=title,
                    description=body[:2000],
                    track=task_track,
                    reward_amount=reward_amount,
                    reward_currency="USD",
                    deadline=deadline,
                    metadata={
                        "platform": "github_bounties_public",
                        "url": html_url,
                        "number": number,
                        "source": "public_discovery",
                    },
                )
                tasks.append(task)
            except Exception as exc:
                logger.debug("[公开发现] 解析 GitHub issue 异常: %s", exc)
                continue

        logger.info("[公开发现] GitHub 解析 %d 个有效任务", len(tasks))
        return tasks

    def _track_keywords(self, track: Track) -> List[str]:
        mapping = {
            Track.ALGORITHM: ["algorithm", "ml", "machine learning", "model", "training", "optimization"],
            Track.DATA_ANALYSIS: ["data", "analysis", "visualization", "dashboard", "eda", "statistics"],
            Track.FRONTEND: ["frontend", "react", "vue", "ui", "component", "css", "html", "javascript"],
            Track.SMART_CONTRACT: ["solidity", "smart contract", "web3", "blockchain", "evm", "contract"],
            Track.DOCS: ["documentation", "readme", "docs", "guide", "tutorial", "api doc"],
            Track.TESTING: ["test", "testing", "e2e", "unit test", "integration test", "qa"],
        }
        return mapping.get(track, [])

    def _build_github_url(self, query: str) -> str:
        from urllib.parse import urlencode
        params = {"q": query, "per_page": self.GITHUB_PER_PAGE, "sort": "updated", "order": "desc"}
        return f"{self.GITHUB_SEARCH_URL}?{urlencode(params)}"

    async def _fetch_json_list(self, url: str) -> List[Dict[str, Any]]:
        now = time.time()
        cached = self._cache.get(url)
        if cached and (now - cached[1]) < self._cache_ttl_seconds:
            return cached[0]

        if self._rate_limited_until and datetime.now(timezone.utc) < self._rate_limited_until:
            logger.debug("[公开发现] GitHub API 限流中，跳过抓取: %s", url)
            return []

        loop = asyncio.get_running_loop()

        def _fetch() -> List[Dict[str, Any]]:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "bounty-hunter-public-discovery/1.0",
                    "Accept": "application/vnd.github+json",
                },
            )
            with urllib.request.urlopen(req, timeout=self._session_timeout) as resp:
                raw = resp.read()
                ct = resp.headers.get("Content-Type", "")
                enc = "utf-8"
                m = re.search(r"charset=([\w-]+)", ct)
                if m:
                    enc = m.group(1)
                text = raw.decode(enc, errors="ignore")
                data = json.loads(text)
                if isinstance(data, dict):
                    return data.get("items", [])
                return data if isinstance(data, list) else []

        try:
            result = await loop.run_in_executor(None, _fetch)
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                try:
                    body = exc.read().decode("utf-8", errors="ignore")
                    data = json.loads(body)
                    msg = data.get("message", "")
                    if "rate limit" in msg.lower():
                        reset_header = exc.headers.get("X-RateLimit-Reset")
                        if reset_header:
                            try:
                                self._rate_limited_until = datetime.fromtimestamp(
                                    int(reset_header), tz=timezone.utc
                                )
                            except ValueError:
                                self._rate_limited_until = datetime.now(timezone.utc) + timedelta(hours=1)
                        else:
                            self._rate_limited_until = datetime.now(timezone.utc) + timedelta(hours=1)
                except Exception:
                    self._rate_limited_until = datetime.now(timezone.utc) + timedelta(hours=1)
            logger.warning("[公开发现] 抓取失败 %s: %s", url, exc)
            return []
        except Exception as exc:
            logger.warning("[公开发现] 抓取异常 %s: %s", url, exc)
            return []

        self._cache[url] = (result, now)
        return result

    def _matches_reject(self, text: str) -> bool:
        low = text.lower()
        reject_keywords = [
            "洗钱", "mixer", "混币", "钱包盗", "seed phrase", "私钥", "private key",
            "刷单", "刷量", "fake order", "wash trade", "数据造假",
            "虚假身份", "账号买卖", "实名绕过", "身份证生成",
            "破解版", "cracked", "nulled", "代码抄袭",
            "赌博", "博彩", "庞氏", "ponzi", "gambling", "betting", "彩票预测",
            "跨境非法结汇", "地下钱庄",
        ]
        for kw in reject_keywords:
            if kw.lower() in low:
                return True
        return False

    def _extract_reward(self, title: str, body: str) -> float:
        text = f"{title}\n{body}"
        for pattern in self.REWARD_PATTERNS:
            match = pattern.search(text)
            if match:
                try:
                    return float(match.group(1).replace(",", ""))
                except ValueError:
                    continue
        return 0.0

    def _infer_track(self, title: str, body: str) -> Track:
        text = f"{title} {body}".lower()
        scores: Dict[Track, int] = {track: 0 for track in Track}
        for track, keywords in {
            Track.ALGORITHM: ["algorithm", "ml", "machine learning", "model", "training", "optimization"],
            Track.DATA_ANALYSIS: ["data", "analysis", "visualization", "dashboard", "eda", "statistics"],
            Track.FRONTEND: ["frontend", "react", "vue", "ui", "component", "css", "html", "javascript"],
            Track.SMART_CONTRACT: ["solidity", "smart contract", "web3", "blockchain", "evm", "contract"],
            Track.DOCS: ["documentation", "readme", "docs", "guide", "tutorial", "api doc"],
            Track.TESTING: ["test", "testing", "e2e", "unit test", "integration test", "qa"],
        }.items():
            for kw in keywords:
                if kw in text:
                    scores[track] += 1
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else Track.ALGORITHM

    def _parse_deadline(self, created_at: Optional[str]) -> datetime:
        if not created_at:
            return datetime.max
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            return dt + timedelta(days=30)
        except Exception:
            return datetime.max

    async def claim_task(self, task_id: str) -> bool:
        """GitHub 公开 Issue 无显式认领，直接标记已认领"""
        logger.info(f"GitHub 公开任务认领: {task_id}")
        return True

    async def submit_task(self, task_id: str, artifacts: List[str]) -> SubmissionResult:
        """提交成果：通过 GitHub PR 提交 (需手动或 CI 完成，此处记录成果文件)"""
        if not artifacts:
            return SubmissionResult(success=False, error="无成果文件")
        logger.info(f"GitHub 公开任务提交: {task_id}, 成果文件: {artifacts}")
        return SubmissionResult(success=True, submission_id=task_id, artifacts=artifacts)

    async def check_task_status(self, task_id: str) -> TaskStatus:
        """查询任务状态"""
        return TaskStatus.SUBMITTED

    async def withdraw(self, amount: float, currency: str, destination: Dict[str, Any]) -> WithdrawalResult:
        """GitHub 公开 bounty 提现通过平台自行处理，不支持 API 直接提现"""
        return WithdrawalResult(
            success=False,
            error="GitHub 公开 bounty 提现需在 GitHub Sponsors / 平台页面手动操作",
        )

    async def get_account_balance(self) -> float:
        return 0.0

    async def get_account_info(self) -> AccountInfo:
        return AccountInfo(
            platform="github_bounties_public",
            username="public",
            balance_usd=0.0,
            kyc_status=False,
            withdrawal_methods=["github_sponsors"],
            is_active=True,
        )

    async def health_check(self) -> bool:
        return self._authenticated

    async def close(self):
        pass

---
name: automated-virtual-goods-pipeline
description: "Use for 4-phase virtual goods pipelines on Xianyu/Tieba."
category: devops
tags: [automation, pipeline, xianyu, virtual-goods, ecommerce, pyxianyu, compliance]
version: 1.0.0
---

# Automated Virtual Goods Pipeline

**Class-level skill for building end-to-end automated pipelines that discover, source, list, and deliver virtual/digital goods on marketplace platforms (闲鱼/Xianyu, Tieba, etc.).**

## When to Use

- Building a complete automated pipeline for selling virtual goods (templates, courses, digital assets, configs, etc.) on Chinese marketplace platforms
- Need to go from product discovery → compliant sourcing → automated listing → hands-free delivery → after-sales automation
- Working with platforms that have unofficial APIs (pyxianyu for Xianyu, aiotieba for Tieba, etc.)
- Need to stay compliant: avoid copyright infringement, sensitive word filtering, platform risk controls

## Core Architecture (4-Phase Pipeline)

```
Phase 1 (Selection Radar) -> Phase 2 (Sourcing Factory) -> Phase 3 (Listing Engine) -> Phase 4 (Delivery Service)
```

### Phase 1: Selection Radar
- **Input**: Keywords, price range, sort criteria, region filters
- **Tool**: `pyxianyu.SearchApi` + custom hot-score algorithm
- **Output**: Ranked product signals (CSV/Excel/JSON) with category, competition, risk flags
- **Key metrics**: `want_view_ratio`, `price_advantage`, `hot_score`, `risk_flags`

### Phase 2: Sourcing Factory
- **Sources**: GitHub Awesome lists (MIT/CC0/Apache-2.0/BSD), official gov templates (著作权法第五条)
- **Legal Gate**: Every source must pass `legal_gate.check_resource()` — license verified, domain whitelisted, no NC/ND/copyleft/ambiguity
- **Processing**: Content deduplication (SHA256), secondary processing (integrate/tutorial/package/audit), standardized packaging (ZIP + INDEX.json)
- **Output**: `sellable_manifest_*.json` (ONLY legal sources) + `legal_audit_*.json` (per-item audit trail)
- **Competitor data**: ONLY in `market_intel_*.json` (reference, physically isolated from sellable pipeline)

### Phase 2.5: Fulfillment Publisher (`src/factory_publish.py`)

**The half that's usually missing.** Phase 2 only emits `download_todo_*.xlsx` (a manual to-do list). Phase 2.5 actually turns verified sources into deliverable product:

```
legal-verified candidate
  → re-verify via legal_gate.check_resource()   (fail-closed, per item)
  → download (GitHub only — NEVER gov sites)
  → differentiator: integrate / process / tutorial / package → ZIP + INDEX.json
  → upload to Baidu netdisk (BDUSS Web API)
  → create share link + 提取码
  → write deliverable_manifest_*.json (netdisk_url / netdisk_pwd + delivery{})
```

- **Only `source == "github"` is auto-downloaded**; official/gov entries are marked `need_manual` and never scraped
- Download size cap; **manual safe tar extraction** (path-traversal guard — `tarfile` `filter='data'` needs 3.12+, don't assume it)
- Per-item failure isolation — one bad repo must not kill the batch
- CLI: `python main.py publish --manifest sellable_manifest_*.json --only-github --limit 5`
- **Top-level `netdisk_url`/`netdisk_pwd` aliases** must be written alongside `delivery{}` — Phase 3 reads top-level

### Phase 3: Listing Engine

- **Template system**: Title templates (30-char limit), description templates per category, SKU price ladders, cover image generation
- **Publishing modes**:
  - `api` — real publish via goofish-cli MCP (`item_publish`)
  - `fishops` — CSV export (`export_fishops_csv()`), human-confirmed bulk import. **Safe default for unattended runs**
- **Compliance**: Sensitive word auto-replacement, virtual goods flag
- **Three hard gates + one delivery gate** in `load_tasks_from_factory()`: filename prefix allowlist (`sellable_manifest_` / `deliverable_manifest_`) → per-item legal re-verify → **virtual goods must carry a real delivery link** → fail-closed

#### goofish-cli internals (verified by source inspection, v in `.venv`)

| Fact | Detail |
|------|--------|
| `cookies.json` | **Encrypted store, NOT JSON** — `json.load()` fails. Use `goofish_cli.core.session.Session.load()` |
| It's MCP-only | `goofish-cli` has **no CLI subcommands**; bare invocation starts a stdio MCP server |
| APIs | read `mtop.idle.web.xyh.item.list` / write `mtop.idle.pc.idleitem.publish` / read `mtop.taobao.idle.pc.detail` |
| `search.items` | goes through a **browser path** (anti-risk-control), not mtop |
| Built-in pacing | `item.write` = **1/min**, `media.write` = 9/min — tune via `GOOFISH_WRITE_RPM` / `GOOFISH_MEDIA_WRITE_RPM` |
| Circuit breaker | auto-trips on risk-control (`core/guard.py`), cooldown `GOOFISH_CIRCUIT_BREAK_MINUTES` (default 10) |
| `appKey` | `34839810`, host `h5api.m.goofish.com` |
| Risk keywords | `_RISK_KEYWORDS = (RGV587_ERROR, FAIL_SYS_USER_VALIDATE, 哎哟喂, /punish)` |
| Auth keywords | `_AUTH_KEYWORDS = (FAIL_SYS_SESSION_EXPIRED, FAIL_SYS_TOKEN_EXOIRED, FAIL_SYS_TOKEN_EMPTY, 令牌过期, FAIL_SYS_ILLEGAL_ACCESS)` |
| Category | `category_json` needs **real numeric** `cat_id`/`channel_cat_id`/`tb_cat_id`. Passing a Chinese category name silently mis-categorizes → **omit `category_json`** and let the built-in `category.recommend(title, images)` auto-detect |
| Cookie refresh | via MCP `auth_login(source=<cookie string>, raw=true)`. **Hammering this triggers risk control** — max once per run |

#### Unattended-safe publish error handling (`publish_task` / `run_listing`)

Never blanket-catch to "failed". Classify the flattened error text:

| Class | Action |
|-------|--------|
| `limited` | parse `retry_after` (regex `再等 ([\d.]+)s`), sleep + jitter, **retry same item** |
| `risk` | set `status='blocked_risk'` → **abort the whole batch**, mark rest `skipped_risk` (circuit already open; continuing makes it worse) |
| `auth` | refresh cookie **once** per run, then continue |
| `other` | mark failed, continue next item |

#### Safe verification without publishing

`tests/probe_publish_stages.py` really runs every write-path step **except the final submit** (image upload → `category.recommend` → `location.default` → build payload). This proves the path works while creating zero listings. Use it to distinguish "link is broken" from "transient risk control" — a healthy run takes ~0.6s per stage and returns a real numeric category.

### Phase 4: Delivery Service
- **Order discovery**: WebSocket real-time (`XianyuLive`) + cron polling compensation
- **Idempotency**: Processed order ID set (persisted JSON) prevents duplicate fulfillment
- **Dual-channel delivery**: 发货凭证 (order receipt) + 私聊 (chat message) - 99%+ reach
- **Card code management**: Atomic reserve/commit/rollback via per-package asyncio locks
- **After-sales**: Keyword auto-reply, delayed 5-star review, daily polish (擦亮), stats push (Feishu/DingTalk/Telegram)

## Compliance Guardrails (Non-Negotiable)

| Red Line | Automated Enforcement |
|----------|----------------------|
| Copyrighted courses/cracks/video | Source allowlist only (GitHub Awesome MIT/CC0/Apache-2.0/BSD, gov templates) |
| 「课程/教程/破解/共享」keywords | `SENSITIVE_WORD_MAP` auto-replace at publish time |
| WeChat/QQ/contact leakage | Delivery channels restricted to platform receipt + chat |
| Single-device multi-account | `ENFORCE_SINGLE_ACCOUNT` config + runtime warning |
| Card code oversell/undership | Per-SKU asyncio lock + file-backed inventory with reserve/commit |
| **Unverified license / NC / ND / copyleft / ambiguous license** | `legal_gate.check_resource()` hard gate — fail-closed |
| **Competitor data entering sellable pipeline** | Phase 3 only accepts `sellable_manifest_*.json` prefix; old manifests rejected |
| **Fake quantity claims in title/description** | `validate_no_false_claims()` auto-check against real `stats`/`items` |
| **Government site scraping** | PROHIBITED — only API-verified GitHub/CC0 sources allowed |

## Configuration Schema

All phases driven by `config/.env` (loaded via `src/config_loader.py` with typed dataclasses):

```bash
# Phase 1
MONITOR_KEYWORDS="PPT模板,Excel表格,合同模板,考公资料"
MONITOR_PRICE_MAX=50
MONITOR_SORT_BY="want_count"

# Phase 2
GITHUB_TOKEN="ghp_xxx"
NETDISK_TYPE="quark"
NETDISK_COOKIE="xxx"

# Phase 3
DAILY_LIST_LIMIT=10
LIST_INTERVAL_MIN=30
SENSITIVE_WORD_MAP='{"课程":"资料包","教程":"学习合集","百度网盘":"某盘"}'

# Phase 4
DELIVERY_MODE="standalone"  # or xianyusmart/xianguanjia
DELIVERY_CONTENT_MODE="netdisk"
AUTO_REVIEW_TEMPLATES='["...","..."]'
```

## Deployment Options

| Mode | Command | Use Case |
|------|---------|----------|
| Interactive CLI | `python main.py menu` | First run, ad-hoc runs |
| One-shot pipeline | `python main.py run --pages 3 --limit 10` | Batch execution |
| Phase-specific | `python main.py select/factory/list/deliver` | Incremental development |
| Docker (delivery) | `docker compose up -d xianyu-delivery` | 7x24 production |
| Docker (scheduler) | `docker compose --profile scheduler up -d xianyu-scheduler` | Daily cron |
| Systemd (WSL2) | `systemctl --user start xianyu-pipeline` | Lightweight background |

## Project Structure

```
xianyu_pipeline/
├── config/
│   ├── .env.example          # Template (copy to .env)
│   └── .env                  # Runtime (gitignored)
├── src/
│   ├── config_loader.py      # Typed config (env > yaml > defaults)
│   ├── phase1_selector.py    # Selection radar
│   ├── phase2_factory.py     # Sourcing factory
│   ├── phase3_lister.py      # Listing engine
│   └── phase4_delivery.py    # Delivery service
├── scripts/
│   └── scheduler.py          # APScheduler cron jobs
├── resources/
│   ├── packages/             # Built ZIP packages
│   ├── cards/                # Card code inventory (package_id.txt)
│   └── covers/               # Generated cover images
├── output/                   # Reports (gitignored)
├── logs/                     # Rotating logs
├── data/
│   └── processed_orders.json # Idempotency key store
├── main.py                   # Unified entry point
├── requirements.txt
├── Dockerfile                # Multi-stage: base/delivery/scheduler/dev
├── docker-compose.yml        # Orchestration
└── README.md                 # Full documentation
```

## Pitfalls & Lessons Learned

1. **Cookie expiry breaks everything** - `pyxianyu` has token auto-refresh but monitor `logs/` for `XianyuApiError: 401` and alert immediately
2. **Netdisk upload APIs are unofficial** - 夸克/百度/阿里 all require reverse-engineered endpoints; prefer manual upload for MVP, automate later
3. **FishOps CSV import is more stable than API** - Xianyu's publish API changes frequently; CSV import via browser plugin survives UI changes better
4. **Card code inventory must be file-backed** - SQLite/Redis adds deployment complexity; flat files (`resources/cards/<package_id>.txt`) work for <10k codes
5. **WebSocket disconnects are normal** - Implement exponential backoff reconnect in `_websocket_listener()`; polling compensation catches gaps
6. **Sensitive word list grows over time** - Maintain `SENSITIVE_WORD_MAP` as living config; add new flags from platform violation notices
7. **Daily list limit must respect account age** - New accounts: 5-10; warmed accounts: 20-50; monitor `logs/` for "风控" warnings
8. **`netdisk_baidu.py` needs explicit `load_dotenv()`** - it defined `ENV_PATH` but never loaded it, so `os.getenv("BAIDU_BDUSS")` silently returned `None` while the `.env` was fine. Always verify the client end-to-end (`python3 src/netdisk_baidu.py` prints account/capacity) before blaming credentials.
9. **Baidu share links must be third-party verified** - fetch the share URL **with a cookie-less session** and assert `HTTP 200` + "需要提取码"/`shareid=`. An upload that "succeeded" is not proof the buyer can open it.
10. **`{ } | tee` in a runner script loses every variable set inside** - the whole brace block runs in a subshell, so `P1=$?` never reaches the parent; combined with `set -u` it dies on `unbound variable`. Use `exec > >(tee -a "$REPORT") 2>&1` instead.
11. **Fabricated style words in titles** - a `random.choice(["莫兰迪","ins风","极简",...])` injected claims like "Excel表格合集**ins风**" that no real data supports. **Drop `{style}` from all templates** and filter any template containing it. Only real, evidence-backed numbers/dates may appear.
12. **Category must be a numeric DTO or omitted** - passing `{"cat_id": "Excel表格"}` passes validation but mis-categorizes. Omit and let `category.recommend` decide.
13. **HTTP 420 + PNG/GIF response ≠ broken pipeline** - it's the anti-bot layer serving a challenge image. Confirm with a read-only mtop probe (`item.list`) and `~/.goofish-cli/circuit.json`; a healthy session answers in ~1s. Root cause is usually request pace (e.g. repeated `auth_login`), not the code.
14. **Don't ship an unattended auto-publish daemon by default** - creating real listings is irreversible and carries risk-control + legal exposure. Deploy the timer with `fishops` (CSV only), gate real publishing behind an explicit `XIANYU_AUTO_PUBLISH=1`, and tell the user the switch exists.
15. **Deterministic ZIP names are not enough — shares still accumulate** - `differentiator` names packages `{slug(title)}.zip`, so re-uploads overwrite the same remote file (good). But **every run calls `create_share()` and creates a NEW shareid** — Baidu caps shares per account, so a daily timer will exhaust it. Keep `resources/packages/published_registry.json` (`source_url` → share link + `published_at`) with a TTL (30d) and **short-circuit `publish_one` on a registry hit** — reuse the old link instead of re-downloading/re-uploading/re-sharing. Backfill it from existing manifests when adding this to a running system, or the first post-change run creates a whole useless round of shares. A reused run drops from ~60s to ~1s.
16. **Playwright `channel="chrome"` on Windows only resolves user-level path** - it looks **only** at `%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe` (not `Program Files`). System-level installs are invisible. Solution: extract real Chrome from official installer (`ChromeStandaloneSetup64.exe` → 7z → `updater.7z` → `chrome.7z` → `Chrome-bin/chrome.exe`) and place at the user-level path. Use a **directory junction** (`C:\Users\...\AppData\Local\Google\Chrome ==> D:\Ai\Google\Chrome`) to keep the 492 MB payload on D: drive. Verify with `playwright install chrome --dry-run` (shows `<system>` location) and `p.chromium.launch(channel="chrome")` actually starting.
20. **Download truncation is silent** - partial downloads (66 MB vs 160 MB expected) pass `MZ`/`PE` header checks but fail at runtime with `exit code 5` and `此应用无法在你的电脑上运行`. **Always verify `Content-Length` from server (`curl -IL`) against local file size** before trusting a binary. Use `curl -C -` (resume) to complete truncated downloads instead of re-downloading.

21. **Firefox cookies auto-imported by goofish-cli** - `goofish_cli.core.session.Session.load()` automatically imports Firefox cookies to `~/.goofish-cli/cookies.json` (log: "已从 firefox 自动导入登录态"). No manual cookie export needed if Firefox is logged in. Phase 1 token self-heal (`src/xianyu_session.py` sync_server_token + call_with_token_refresh) works in production and aligns `_m_h5_tk` with server in real time.

22. **Playwright channel="chrome" on Windows only resolves user-level path** - it looks **only** at `%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe` (not `Program Files`). System-level installs are invisible. Solution: extract real Chrome from official installer (`ChromeStandaloneSetup64.exe` → 7z → `updater.7z` → `chrome.7z` → `Chrome-bin/chrome.exe`) and place at the user-level path. Use a **directory junction** (`C:\Users\...\AppData\Local\Google\Chrome ==> D:\Ai\Google\Chrome`) to keep the 492 MB payload on D: drive. Verify with `playwright install chrome --dry-run` (shows `<system>` location) and `p.chromium.launch(channel="chrome")` actually starting.

23. **Hard timeout protection is mandatory for scheduled pipelines** - the full pipeline (17 min) and each phase must have wall-clock timeouts to prevent stuck cron jobs. Created `src/timeout_utils.py` with `with_timeout(coro, timeout, operation)`, decorators (`@timeout_protected`), and context managers. Wrap every Phase entry in `main.py` with `with_timeout(inner, PHASE*_TIMEOUT)`. Configure via env: `XY_PIPELINE_TIMEOUT=1800`, `XY_PHASE1_TIMEOUT=600`, `XY_PHASE2_TIMEOUT=900`, `XY_PHASE25_TIMEOUT=1200`, `XY_PHASE3_TIMEOUT=600`, `XY_MCP_TIMEOUT=60`, `XY_SEARCH_TIMEOUT=30`, `XY_DOWNLOAD_TIMEOUT=300`, `XY_UPLOAD_TIMEOUT=300`, `XY_NETDISK_SHARE_TIMEOUT=120`.

**Implementation pattern** (in `main.py`):
```python
from src.timeout_utils import with_timeout, PHASE1_TIMEOUT, PHASE2_TIMEOUT, PHASE25_TIMEOUT, PHASE3_TIMEOUT, GLOBAL_PIPELINE_TIMEOUT

async def run_phase1_selection(self, pages=3) -> dict:
    return await with_timeout(
        self._run_phase1_selection_inner(pages),
        timeout=PHASE1_TIMEOUT,
        operation="Phase1:选品雷达",
        on_timeout=lambda: logger.warning("Phase1 超时")
    )
```
**Fine-grained timeouts** in phase modules:
- `phase1_selector.py`: `with_timeout(asyncio.to_thread(call_with_token_refresh, ...), SEARCH_PAGE_TIMEOUT)` per search page
- `phase2_factory.py`: `with_timeout(self._fetch_single_repo(...), MCP_CALL_TIMEOUT)` per GitHub repo, `with_timeout(asyncio.to_thread(verify_url), MCP_CALL_TIMEOUT)` per official source
- `netdisk_baidu.py`: retry logic handles share timeout, `with_timeout` not needed (requests has native timeout)
- Phase 4: per-poll timeout via `PHASE4_POLL_TIMEOUT * 10` window

24. **Phase 3 "0 success" means publish async needs confirmation** - items were published but returned no `status="success"`. The MCP `item_publish` likely returns a task ID requiring follow-up polling. Check `run_listing` logic: it records success only if `result.get("status") == "success"`. Need to implement post-publish status polling or webhook confirmation.

**FIXED** - Root cause was **MCP result parsing**, not async confirmation. The goofish-cli `item_publish` returns a nested MCP result where `item_id` lives in `structuredContent.data.item_id` or `content[0].text -> JSON -> data.item_id`, NOT directly in `result.data`. The `publish_task` method expected `result.data.get("item_id")` but the actual structure is:
```python
# result.data is the full MCP result object:
{
  "structuredContent": {"data": {"item_id": "12345", "itemId": "12345"}},
  "content": [{"text": "{\"data\":{\"item_id\":\"12345\"}}"}]
}
```
**Fix** in `phase3_lister.py` `publish_task()`:
```python
if result.success:
    item_id = ""
    data = result.data
    if isinstance(data, dict):
        # 1. structuredContent.data.item_id
        structured = data.get("structuredContent", {})
        if isinstance(structured, dict):
            inner = structured.get("data", {})
            if isinstance(inner, dict):
                item_id = inner.get("item_id", inner.get("itemId", ""))
        # 2. content[0].text -> JSON -> data.item_id
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
        # 3. fallback: direct data.item_id
        if not item_id:
            item_id = data.get("item_id", data.get("itemId", ""))
    if item_id:
        task.item_id = item_id
        task.status = "success"
        ...
```

25. **Baidu netdisk `create_share` errno=115 = share already exists / rate limit / permission** - multiple files uploaded successfully but share creation failed. Add exponential backoff retry + fs_id caching. On 115, try fetching existing shares for that fs_id before retrying. The `published_registry` pattern (pitfall 15) also prevents re-sharing the same file.

**IMPLEMENTED** in `src/netdisk_baidu.py` `create_share()`:
```python
max_retries = 3
base_delay = 2.0
last_err = None

for attempt in range(1, max_retries + 1):
    try:
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
        logger.success(f"分享创建成功: {link}")
        return {"link": link, "pwd": pwd_ret, "shareid": shareid, "uk": j.get("uk")}

    # errno=115: 可能是已分享、频控、权限不足 —— 可重试
    if errno == 115 or error_code == 115:
        logger.warning(f"创建分享 errno=115 (尝试 {attempt}/{max_retries}): {j.get('errmsg')}")
        last_err = NetdiskShareError(fs_ids, f"errno=115: {j.get('errmsg')}")
        if attempt < max_retries:
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
            logger.info(f"  等待 {delay:.1f}s 后重试...")
            time.sleep(delay)
        continue

    # 其他错误直接抛出
    raise NetdiskShareError(fs_ids, f"创建分享失败 errno={errno}")

raise NetdiskShareError(fs_ids, f"创建分享重试 {max_retries} 次均失败") from last_err
```

26. **Structured streaming logs needed for observability** - current `loguru` writes human-readable text only. Add JSON Lines sink (`serialize=True`) for Loki/Vector/Grafana ingestion. Emit structured events: `phase_start`, `phase_end`, `item_start`, `item_end`, `error` with `trace_id`/`span_id` for distributed tracing.

27. **ResourceFactory must store MCP client as `self.mcp`** - `PhaseTools` wraps `MCPClient` as `self.mcp`. `ResourceFactory.__init__` received `mcp_client` but only passed it to `PhaseTools(mcp_client)` as `self.mcp_tools`. When `fetch_pan_resources()` later accessed `self.mcp`, it raised `AttributeError`. **Fix**: add `self.mcp = mcp_client` in `__init__` before creating `self.mcp_tools`.

28. **Billing system integration** - Added `src/billing/TokenCounter` with DeepSeek-V3 official CNY pricing (Input ¥0.001/1K, Output ¥0.002/1K). Only charges in production mode (`set_production_mode(True)`) with a valid `order_id`. Debug/test runs cost ¥0. `CSOrchestrator` auto-records token usage per reply generation in production mode. Usage: `from src.billing import get_token_counter; c = get_token_counter(); c.set_production_mode(True); c.record(order_id, service, operation, input_t, out_t)`.

29. **Customer service module (`src/service_cs/`)** - New package: `cs_orchestrator` (main loop), `intent_router` (price/bargain/delivery/refund/complaint classification), `pricing_engine` (floor/max_discount/max_rounds by category), `reply_generator` (templates validated by `ServiceTalkValidator`), `human_handoff` (amount threshold, risk keywords, efficiency, refund disputes). Integrates with `TokenCounter` for per-order cost tracking.

30. **Preflight check is the gate before every full pipeline run** - `scripts/preflight_check.py` validates three hard preconditions in <10s: (1) Xianyu business API (`item_list` returns items — `auth_status` has false negatives), (2) Media upload subdomain (`stream-upload.goofish.com` requires `cookie2`/`_tb_token_` session cookies), (3) Netdisk share capability (prefers official `bdpan` OAuth, falls back to BDUSS with errno=115 detection). Any failure → exit code 2 → caller skips pipeline. Run with `--fix-cookie` to auto-sync Firefox cookies first.

31. **Phase 2 pan-search is opt-in only** - The `fetch_pan_resources()` loop iterates 17 categories × multiple keywords, each pan-search MCP call takes ~80s, totaling >15 min and exceeding the 900s Phase 2 timeout. **Fix**: gate behind `ENABLE_PAN_SEARCH=1` env var (default OFF). Only GitHub Awesome + official sources run by default. Phase 2.5 `factory_publish.py` already reuses existing netdisk shares via `published_registry` — pan-search is a discovery channel, not a fulfillment channel.

32. **MCPToolResult is not JSON serializable** - `fetch_competitor_resources()` stored raw `MCPToolResult` objects in `detail_data`, causing `TypeError` when writing `market_intel_*.json`. **Fix**: before appending to resources list, convert: if has `success`/`data`/`error` attributes, extract to plain dict; else try `dict()`; else fallback to `str()`. This keeps the log serializable while preserving error info.

33. **Baidu netdisk share registry prevents re-sharing** - `factory_publish.py` maintains `published_registry.json` mapping `source_url` → share link + `published_at` (TTL 30d). On registry hit, `publish_one` short-circuits: reuses old link instead of re-downloading/uploading/sharing. A reused run drops from ~60s to ~1s and avoids exhausting Baidu's per-account share quota. Backfill from existing manifests when adding to a running system, or the first post-change run creates a useless round of shares.

34. **`pre_listing_quality_gate` must preserve the input TYPE — returning dicts silently breaks Phase 3** - `load_tasks_from_factory()` emits `ListingTask` dataclasses, but `pre_listing_quality_gate()` did `item.copy()` + `item["title"]=...` and returned **dicts**. Downstream `publish_task(task: ListingTask)` uses **attribute access** (`task.title` / `task.images` / `task.sku_list`), so dicts die with `'ListingTask' object has no attribute 'copy'` (and `'dict' object has no attribute 'title'` one step later).
   **Fix — be type-preserving**: branch on `hasattr(item, "__dataclass_fields__")`; for dataclasses set a real `quality_report: Dict = field(default_factory=dict)` field on the dataclass (works because `ListingTask` has no `slots=`), for dicts keep the old keyed path. Callers must read the report type-agnostically:
   ```python
   def _qp(t):
       if hasattr(t, "__dataclass_fields__"):
           return bool((t.quality_report or {}).get("passed", False))
       return bool(t.get("_quality_report", {}).get("passed", False))
   ```

35. **The quality gate's "fix" is a SERVICE template — applying it to goods silently converts the listing and destroys all SEO** - `generate_seo_title()` produced `Excel代做 函数公式 数据清洗 个人接单·不满意免费微调` and `clean_description()`+`generate_marketing_desc()` replaced curated copy. The gate applied these **unconditionally**, turning a "sell a tool package" listing into "sell a service", wiping every researched keyword from title and body. It passes `report.passed=True` and reports `seo_score: 35/100` while doing it, so nothing looks wrong in the log.
   **Rule — a gate may only fix what is actually broken**: for the goods path (dataclass with curated content) apply `fixed_title`/`fixed_desc` **only when `not report.passed`** (hard fail = banned word / category error / ellipsis); otherwise keep the curated title/desc and just attach the report. Service listings (dict path, where the gate legitimately generates copy from scratch) keep the always-overwrite behaviour. Also note `category_json` is **irrelevant on the `api` publish path** — `publish_task` resolves it live via `_resolve_category(title, image_urls)`; category only matters for the FishOps CSV export.

36. **`original_price` / 划线价 is local-report-only — never fabricated-and-submitted** - `_generate_sku` set `original_price = base_price * 3`, which reads like an invented strike-through price. Verified in source: the publish payload sends **only** `"price": task.price`; `original_price` appears solely in the local report (`原价`). So no fabricated reference price reaches buyers — but **re-check this on every pipeline change**: if `original_price` ever enters the submit payload, an arbitrary 3× multiple becomes false-price advertising and must be dropped, not tuned.

37. **Curated SEO content needs explicit override hooks, each with fail-safe validation** - to let a manifest supply hand-written marketing copy, add four hooks in `phase3_lister.py`, and make **every one fall back to the template on invalid input** (never publish unvalidated text, never crash the batch):

   | Hook | Manifest field | Validation before use |
   |------|---------------|----------------------|
   | `_generate_title` | `seo_title` | ≤30 chars + banned-word scan |
   | `_generate_description` | `seo_desc` | `validate_no_false_claims()` (real numbers only) + legal-citation leak check |
   | `_generate_sku` | `seo_sku` | ≥1 tier, positive price, non-empty name |
   | `_prepare_images` | `cover_images` | each path exists and file size > 0 |

   **The call site must forward the resource** — `_generate_sku(category, res)`, not `_generate_sku(category)`; changing only the signature leaves the hook dead and the default ladder silently wins. Verify a hook actually fired by printing/logging on the override path, then diff the produced `ListingTask` — do not assume a signature change took effect.
   Keep legal citations (法条依据) in an internal `LEGAL_BASIS` only; run the leak check so they can never reach buyer-visible copy.

38. **Verify a publish by reading the live list back, matching `item_id` — not by trusting the return value** - `main.py list` reported `✅ Phase 3 完成: 上架 1 个` and the result JSON said `status=success, item_id=1092328365607`. Independent confirmation came from calling the read-only `goofish.item_list` MCP tool: `ok=True`, 39 items on sale, and the first row was the exact title at `¥9.90` with the **same `item_id`**. A publish "success" is a claim; the `item_list` row is proof. (Note `item_list` rows expose `item_id`/`title`/`price`/`status`/`image_url`/`rank` — `status: -9` is normal for an on-sale item.)

## Extension Points
19. **Phase 3 "0 success" means publish async needs confirmation** - items were published but returned no `status="success"`. The MCP `item_publish` likely returns a task ID requiring follow-up polling. Check `run_listing` logic: it records success only if `result.get("status") == "success"`. Need to implement post-publish status polling or webhook confirmation.
20. **Baidu netdisk `create_share` errno=115 = share already exists / rate limit / permission** - multiple files uploaded successfully but share creation failed. Add exponential backoff retry + fs_id caching. On 115, try fetching existing shares for that fs_id before retrying. The `published_registry` pattern (pitfall 15) also prevents re-sharing the same file.
21. **Structured streaming logs needed for observability** - current `loguru` writes human-readable text only. Add JSON Lines sink (`serialize=True`) for Loki/Vector/Grafana ingestion. Emit structured events: `phase_start`, `phase_end`, `item_start`, `item_end`, `error` with `trace_id`/`span_id` for distributed tracing.

## Extension Points

- **New platform**: Implement `BasePlatformAdapter` with `search`, `publish`, `deliver`, `poll_orders` methods
- **New sourcing channel**: Add fetcher in `phase2_factory.py` returning standardized resource dicts
- **New delivery channel**: Implement `DeliveryChannel` enum value + `_send_<channel>_delivery()` method
- **New after-sales action**: Register handler in `_handle_buyer_message()` keyword router

## Related Skills

- `hermes-script-library-safety` - WSL2 script safety (guard.py, readonly mounts) for pipeline script development
- `configure-mcp-servers` - If exposing pipeline as MCP tools for AI agents
- `manage-python-venv-wsl` - Virtual environment management in WSL2

## References

- `references/xianyu-api-quirk.md` - pyxianyu version-specific quirks, error codes, rate limits
- `references/compliance-checklist.md` - Platform rule change log, sensitive word evolution
- `references/deployment-notes.md` - Docker/systemd/WSL2 deployment gotchas
- `references/chrome-windows-junction.md` - Playwright channel="chrome" on Windows: user-level path + D: drive junction setup
- `references/timeout-config.md` - Hard timeout configuration for all pipeline phases

## Templates

- `templates/.env.example` - Full configuration template (copied to `config/.env.example`)
- `templates/docker-compose.yml` - Production docker-compose (copied to root)
- `templates/systemd-service.conf` - Systemd user service unit
- `templates/timeout-config.env` - Timeout environment variable template

## Scripts

- `scripts/verify_pyxianyu.py` - Smoke test for pyxianyu connectivity (cookie valid, search works, publish dry-run)
- `scripts/cookie_refresh.py` - Automated cookie refresh via headless browser (Playwright)
- `scripts/netdisk_upload.py` - Netdisk upload CLI (夸克/百度/阿里)
- `scripts/extract_chrome_windows.py` - Extract real Chrome from Google installer 7z payload and place at user-level path
- `scripts/verify_timeouts.py` - Verify all Phase timeouts are configured and reachable
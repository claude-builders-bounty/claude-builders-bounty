# Hard Timeout Configuration for Xianyu Pipeline

## Overview
All pipeline phases and critical operations must have wall-clock timeouts to prevent stuck cron jobs. Created `src/timeout_utils.py` with centralized timeout management.

## Timeout Values (Environment Variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `XY_PIPELINE_TIMEOUT` | 1800s (30 min) | Full pipeline (Phase 1-3) |
| `XY_PHASE1_TIMEOUT` | 600s (10 min) | Phase 1: Selection Radar |
| `XY_PHASE2_TIMEOUT` | 900s (15 min) | Phase 2: Sourcing Factory |
| `XY_PHASE25_TIMEOUT` | 1200s (20 min) | Phase 2.5: Fulfillment Publisher |
| `XY_PHASE3_TIMEOUT` | 600s (10 min) | Phase 3: Listing Engine |
| `XY_PHASE4_POLL_TIMEOUT` | 30s | Phase 4: Single poll cycle |
| `XY_MCP_TIMEOUT` | 60s | Single MCP tool call |
| `XY_SEARCH_TIMEOUT` | 30s | Single page search (pyxianyu) |
| `XY_DOWNLOAD_TIMEOUT` | 300s (5 min) | Single file download (GitHub release) |
| `XY_UPLOAD_TIMEOUT` | 300s (5 min) | Single file upload (netdisk) |
| `XY_NETDISK_SHARE_TIMEOUT` | 120s (2 min) | Baidu share link creation |

## Usage Patterns

### 1. Phase Entry Wrapper (in `main.py`)
```python
from src.timeout_utils import with_timeout, PHASE1_TIMEOUT

async def run_phase1_selection(self, pages: int = 3, output: str = "output") -> dict:
    return await with_timeout(
        self._run_phase1_selection_inner(pages, output),
        timeout=PHASE1_TIMEOUT,
        operation="Phase1:选品雷达",
        on_timeout=lambda: logger.warning("Phase1 超时，已中断")
    )
```

### 2. Fine-grained Operation (in `phase1_selector.py`)
```python
from src.timeout_utils import with_timeout, SEARCH_PAGE_TIMEOUT

result = await with_timeout(
    asyncio.to_thread(call_with_token_refresh, ...),
    timeout=SEARCH_PAGE_TIMEOUT,
    operation=f"search:{keyword}:p{page}"
)
```

### 3. MCP Call Protection (in `phase2_factory.py`)
```python
from src.timeout_utils import with_timeout, MCP_CALL_TIMEOUT

v = await with_timeout(
    asyncio.to_thread(self._verify_url_live, url),
    timeout=MCP_CALL_TIMEOUT,
    operation=f"OfficialVerify:{name}"
)
```

### 4. Decorator Form
```python
from src.timeout_utils import timeout_protected, phase1_timeout

@phase1_timeout
async def run_selection(self, pages_per_keyword: int = 3):
    ...
```

## Phase 4 (Long-running Service)
Phase 4 uses per-poll timeout:
```python
from src.timeout_utils import PHASE4_POLL_TIMEOUT, with_timeout

await with_timeout(
    self.phase4_delivery.run(),
    timeout=PHASE4_POLL_TIMEOUT * 10,  # Allow 10 poll cycles
    operation="Phase4:发货轮询"
)
```

## Verification
Run `python scripts/verify_timeouts.py` to check all timeouts are reachable and not causing false positives.

## Key Principle
**Every external I/O and every phase entry must have a timeout.** No bare `await` on unbounded operations in scheduled pipelines.

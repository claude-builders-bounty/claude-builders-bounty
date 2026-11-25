#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify all Phase timeouts are configured and reachable."""

import os
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.timeout_utils import (
    GLOBAL_PIPELINE_TIMEOUT, PHASE1_TIMEOUT, PHASE2_TIMEOUT,
    PHASE25_TIMEOUT, PHASE3_TIMEOUT, PHASE4_POLL_TIMEOUT,
    MCP_CALL_TIMEOUT, SEARCH_PAGE_TIMEOUT,
    DOWNLOAD_TIMEOUT, UPLOAD_TIMEOUT, NETDISK_SHARE_TIMEOUT
)

EXPECTED = {
    "XY_PIPELINE_TIMEOUT": GLOBAL_PIPELINE_TIMEOUT,
    "XY_PHASE1_TIMEOUT": PHASE1_TIMEOUT,
    "XY_PHASE2_TIMEOUT": PHASE2_TIMEOUT,
    "XY_PHASE25_TIMEOUT": PHASE25_TIMEOUT,
    "XY_PHASE3_TIMEOUT": PHASE3_TIMEOUT,
    "XY_PHASE4_POLL_TIMEOUT": PHASE4_POLL_TIMEOUT,
    "XY_MCP_TIMEOUT": MCP_CALL_TIMEOUT,
    "XY_SEARCH_TIMEOUT": SEARCH_PAGE_TIMEOUT,
    "XY_DOWNLOAD_TIMEOUT": DOWNLOAD_TIMEOUT,
    "XY_UPLOAD_TIMEOUT": UPLOAD_TIMEOUT,
    "XY_NETDISK_SHARE_TIMEOUT": NETDISK_SHARE_TIMEOUT,
}

print("=== Timeout Configuration Verification ===")
all_ok = True
for name, default in EXPECTED.items():
    env_val = os.getenv(name)
    actual = int(env_val) if env_val else default
    status = "OK" if actual == default else f"OVERRIDE ({actual}s vs {default}s)"
    print(f"  {name:<30s} = {actual:>5d}s  [{status}]")
    if actual != default:
        all_ok = False

print()
if all_ok:
    print("All timeouts at defaults. Configure via .env if needed.")
else:
    print("Some timeouts overridden - verify they are intentional.")

# Quick smoke test: can we import and use the timeout utils?
print("\n=== Smoke test: with_timeout() ===")
import asyncio
from src.timeout_utils import with_timeout, TimeoutError

async def test():
    try:
        await with_timeout(asyncio.sleep(10), 0.1, "test")
        print("FAIL: should have timed out")
        return False
    except TimeoutError:
        print("PASS: TimeoutError raised correctly")
        return True
    except Exception as e:
        print(f"FAIL: wrong exception: {e}")
        return False

if asyncio.run(test()):
    print("\nAll checks passed.")
    sys.exit(0)
else:
    sys.exit(1)
